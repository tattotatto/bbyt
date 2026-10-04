# 地基修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修掉三处让生产环境的 5 个 tab 页拿不到真实数据的缺陷——缺迁移、前后端契约漂移、零种子数据。

**Architecture:** 三块互不依赖的修复。**B1** 补一个 alembic 迁移，让 schema 与模型对齐，消除 `/promotions/active` 的 500；**B2** 把前端的案例标签、筛选参数、点赞、登出对齐到后端**实际存在**的接口，纯前端改动；**B3** 新增一个幂等种子脚本，按「存在即跳过」写入分类／商品／案例／促销。三者之间没有调用关系，可独立执行、独立回滚。

**Tech Stack:** FastAPI + SQLAlchemy 2.0 async + Alembic + PostgreSQL（`pgvector/pgvector:pg16`）；前端 uni-app + Vue 3 + TypeScript，测试用 vitest；后端测试用 pytest（SQLite 内存库）。

**Spec:** `docs/superpowers/specs/2026-10-04-miniapp-redesign-design.md` — §9 范围边界是本文档的依据；§1「关键前提」是三项缺陷的实测记录。

## Global Constraints

- 品牌主色 `#e16531` 不变。本计划**不碰任何样式文件**。
- 后端测试命令：**`cd backend && venv/Scripts/python -m pytest -q`**。这个环境的 Python 里原本没装后端依赖
  （fastapi/sqlalchemy/asyncpg/pytest/aiosqlite 全缺），`pytest` 也不在 PATH 上。已建好 `backend/venv`
  （Python 3.11；3.14/3.13 太新，`bcrypt==4.0.1` 等固定版本没有对应轮子），装的是 `requirements.txt` 里已有的依赖。
  基线：这套测试在改动前是 **159 passed**。所有后端命令里的 `pytest` 一律换成 `venv/Scripts/python -m pytest`。
- 前端测试命令：`cd miniapp && npm test`
- 后端测试跑 SQLite 内存库（`tests/conftest.py` 用 `Base.metadata.create_all`，**不跑迁移**）；生产是 PostgreSQL。**任何迁移改动都不能只靠 pytest 验证**。
- 新建前端测试文件必须落在 `src/api/__tests__/`、`src/utils/__tests__/` 或 `src/stores/__tests__/` 下，否则 `miniapp/vitest.config.ts` 的 `include` 不会收集它。
- 定价矩阵 `pricing_rules` 的键是**小写等级值** `normal` / `silver` / `gold` / `platinum`（见 `app/services/pricing.py:11` 与 `app/models/user.py:15-19`），不是枚举名。
- 本计划**不做**：积分抽奖、15 个子页面、§9「本次不做」表格里记录的 8 个后端已确认缺陷。
- **不新增任何依赖。**

## Review Focus

Spec 是愿景文档，以下五类输入它没有逐条写明，但恰恰最可能在真实使用中咬人。每一条都已在它所属的任务里配了测试。

1. **迁移在一张已经有 `promotions` 表的库上执行** —— 有人手工建过、或曾用 `create_all` 建过。此时 `alembic upgrade head` 必须不报错。报错会让 `deploy/deploy-prod.sh:81` 中断，整个部署卡死。
2. **迁移回滚后再前滚** —— `alembic downgrade -1` 必须干净地删掉三张表**和两个 PostgreSQL 枚举类型**；紧接着 `upgrade head` 必须再成功。生产回滚时会走这条路。
3. **种子脚本在一张已经有一半数据的库上跑** —— 必须零重复行。空库连跑两遍很容易过，半有半无才是幂等性的真实检验（「分类建了、商品没建」这种中间状态）。
4. **案例标签接口失败或后端仍是旧版本时** —— 案例页的筛选器必须静默降级成「全部」，不能白屏、不能卡在 loading。
5. **`GET /cases/tags` 在零案例的库上** —— 必须返回三个空数组而不是 500，且前端取 `data.style_tags` 不能是 `undefined`。

---

### Task 1: 补写迁移，建 `promotions` / `credit_bills` / `knowledge_entries`

Spec §1 实测：模型定义了 14 张表，迁移只建了 11 张。`/promotions/active` 因此在生产上返回 HTTP 500 `UndefinedTableError: relation "promotions" does not exist`。部署脚本确实在跑 `alembic upgrade head`，但无事可做——**迁移文件根本没写**，所以重跑修不好。

三张表一起做：它们共用同一个根因，一个 reviewer 不会批准 `promotions` 却驳回 `credit_bills`。

**Files:**
- Create: `backend/tests/test_migration_coverage.py`
- Create: `backend/alembic/versions/e5f6a7b8c9d0_add_promotion_bill_knowledge.py`
- Reference（只读，不要改）: `backend/app/models/promotion.py`、`backend/app/models/bill.py`、`backend/app/models/knowledge.py`、`backend/alembic/versions/d4e5f6a7b8c9_add_cart_address_history_favorites.py`

**Interfaces:**
- Consumes: `Base.metadata`（来自 `app.models`，已存在）
- Produces: alembic revision `e5f6a7b8c9d0`（`down_revision = 'd4e5f6a7b8c9'`，即当前 head）；数据库表 `promotions`、`credit_bills`、`knowledge_entries`；PostgreSQL 枚举类型 `promotiontype`、`billstatus`

- [ ] **Step 1: 写守卫测试**

现有测试走 `create_all`，结构上不可能发现「模型有、迁移没有」。这个测试直接比对两份清单，让这类漂移以后一定能被测出来。

创建 `backend/tests/test_migration_coverage.py`：

```python
"""迁移覆盖度守卫：模型定义的每张表，都必须有迁移把它建出来。

回归的是实测出的真实缺陷：模型定义了 14 张表，迁移只建了 11 张，
promotions / credit_bills / knowledge_entries 从未在任何迁移里出现，
生产库因此不存在这三张表，/promotions/active 直接 500。

tests/conftest.py 用 Base.metadata.create_all 建表，所以现有 159 个测试
结构上看不见这个问题——表总是齐全的。这个测试不看数据库，只看源码。
"""
import ast
import re
from pathlib import Path

from app.models import Base

VERSIONS_DIR = Path(__file__).resolve().parent.parent / "alembic" / "versions"

# op.create_table('name', 或 op.create_table("name",
_CREATE_TABLE_RE = re.compile(r"op\.create_table\(\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]")


def _tables_created_by_migrations() -> set[str]:
    tables: set[str] = set()
    for path in VERSIONS_DIR.glob("*.py"):
        tables.update(_CREATE_TABLE_RE.findall(path.read_text(encoding="utf-8")))
    return tables


def test_every_model_table_has_a_migration():
    model_tables = set(Base.metadata.tables)
    migration_tables = _tables_created_by_migrations()

    missing = sorted(model_tables - migration_tables)
    assert missing == [], (
        f"这些表在模型里定义了，但没有任何迁移创建它们：{missing}\n"
        f"后果：生产库不会有这些表，相关接口报 500（deploy 脚本里 "
        f"alembic upgrade head 会成功跑完，因为它确实无事可做）。\n"
        f"修法：在 backend/alembic/versions/ 下新增一个迁移建这些表。"
    )


def test_migration_revision_chain_has_no_gaps():
    """每个 down_revision 都要指向一个真实存在的 revision 或 None。"""
    revisions: dict[str, str | None] = {}
    for path in VERSIONS_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        rev = re.search(r"^revision(?:\s*:\s*str)?\s*=\s*['\"]([^'\"]+)['\"]", text, re.M)
        down = re.search(r"^down_revision(?:\s*:[^=]+)?\s*=\s*(.+)$", text, re.M)
        if not rev or not down:
            continue
        raw = down.group(1).strip()
        parent = None if raw in ("None", "'None'", '"None"') else raw.strip("'\"")
        revisions[rev.group(1)] = parent

    assert revisions, "没有解析到任何 revision，正则可能过期了"

    orphans = sorted(
        f"{rev} -> {parent}"
        for rev, parent in revisions.items()
        if parent is not None and parent not in revisions
    )
    assert orphans == [], f"这些 down_revision 指向不存在的 revision：{orphans}"


# ── 列级守卫 ───────────────────────────────────────────────────────────────────
# 存在的理由：真实 PostgreSQL 上的检查点（干净库前滚 / 回滚再前滚 / 表已存在时前滚）
# 推迟到了服务器，本地只剩 SQLite。而 SQLite 走的是 create_all，根本碰不到迁移。
# 这个测试用 AST 解析迁移源码，把「迁移会建出哪些列、可空性如何」和模型逐列比对，
# 不需要任何数据库 —— 用来补上一部分被推迟掉的保障。
#
# 它覆盖不了什么（这些只有真实 PG 能验）：枚举类型是否真的建出来、downgrade 是否
# 清理干净枚举类型、表已存在时是否会抛 DuplicateTable。别把它当成那些检查点的替代品。

def _str_literal(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _column_from_call(call: ast.Call) -> tuple[str, bool | None] | None:
    """从 sa.Column('name', ..., nullable=False) 里取出 (列名, 是否非空)。

    迁移里没写 nullable= 时返回 None —— 表示「不比较」，而不是猜一个默认值。
    """
    if not isinstance(call.func, ast.Attribute) or call.func.attr != "Column" or not call.args:
        return None
    name = _str_literal(call.args[0])
    if not name:
        return None
    nullable: bool | None = None
    for kw in call.keywords:
        if kw.arg == "nullable" and isinstance(kw.value, ast.Constant):
            nullable = bool(kw.value.value)
    return name, nullable


def _columns_created_by_migrations() -> dict[str, dict[str, bool | None]]:
    """{表名: {列名: 是否非空}}，合并 create_table 与后续的 add_column。"""
    out: dict[str, dict[str, bool | None]] = {}
    for path in VERSIONS_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            attr = getattr(node.func, "attr", None)
            if attr not in ("create_table", "add_column") or not node.args:
                continue
            table = _str_literal(node.args[0])
            if not table:
                continue
            bucket = out.setdefault(table, {})
            for arg in node.args[1:]:
                if isinstance(arg, ast.Call):
                    parsed = _column_from_call(arg)
                    if parsed:
                        bucket[parsed[0]] = parsed[1]
    return out


def test_migration_columns_match_models():
    """迁移建出来的列，必须和模型逐列对得上（列名 + 显式声明的可空性）。"""
    migrated = _columns_created_by_migrations()
    problems: list[str] = []

    for table, model_table in Base.metadata.tables.items():
        if table not in migrated:
            continue  # 缺整张表由 test_every_model_table_has_a_migration 负责
        declared = migrated[table]
        model_cols = set(model_table.columns.keys())

        missing = sorted(model_cols - set(declared))
        extra = sorted(set(declared) - model_cols)
        if missing:
            problems.append(f"{table}: 迁移少了这些列 -> {missing}")
        if extra:
            problems.append(f"{table}: 迁移多了模型里没有的列 -> {extra}")

        for col, nullable in declared.items():
            if nullable is None or col not in model_cols:
                continue
            actual = model_table.columns[col].nullable
            if actual != nullable:
                problems.append(
                    f"{table}.{col}: 迁移写 nullable={nullable}，模型是 nullable={actual}"
                )

    assert problems == [], (
        "迁移与模型的列定义对不上：\n  " + "\n  ".join(problems)
    )
```

- [ ] **Step 2: 跑测试，确认它失败**

```bash
cd backend && venv/Scripts/python -m pytest tests/test_migration_coverage.py -v
```

预期：`test_every_model_table_has_a_migration` **FAIL**，断言消息里列出恰好三张表：

```
AssertionError: 这些表在模型里定义了，但没有任何迁移创建它们：['credit_bills', 'knowledge_entries', 'promotions']
```

`test_migration_revision_chain_has_no_gaps` 应当 PASS。

如果列出的不止这三张，停下来核对——说明还有别的漂移，需要一并纳入本任务。

`test_migration_columns_match_models` 本步应当是 **PASS**（那三张表还不存在任何迁移里，它按设计跳过，
比较不出东西）。它要到 Step 3 写完迁移后才真正开始起作用——Step 4 会验证它确实有牙齿。

- [ ] **Step 3: 写迁移**

创建 `backend/alembic/versions/e5f6a7b8c9d0_add_promotion_bill_knowledge.py`。

列定义逐字对应三个模型文件。`sa.Enum` 的取值用**枚举名**（大写），与既有迁移 `8c774cbe946f` / `c3d4e5f6a7b8` 的写法一致。

```python
"""add_promotion_bill_knowledge

补建三张「模型有、迁移没有」的表：promotions / credit_bills / knowledge_entries。
在此之前生产库不存在这三张表，/promotions/active 返回 500。

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-10-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    """表已存在时跳过建表。

    存在的场景是真的：有人手工建过，或某个环境的表是用
    Base.metadata.create_all 建的。此时如果直接 create_table，
    deploy-prod.sh 里的 alembic upgrade head 会抛 DuplicateTable
    并中断整条部署流水线。
    """
    return sa.inspect(op.get_bind()).has_table(name)


def upgrade() -> None:
    # --- promotions ---
    if not _has_table('promotions'):
        op.create_table(
            'promotions',
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('type', sa.Enum('FULL_REDUCTION', 'DISCOUNT', 'FLASH_SALE', name='promotiontype'), nullable=False),
            sa.Column('rules', sa.JSON(), nullable=False, comment='促销规则'),
            sa.Column('product_ids', sa.JSON(), nullable=True, comment='适用商品ID列表(null=全场)'),
            sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
            sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    # --- credit_bills ---
    if not _has_table('credit_bills'):
        op.create_table(
            'credit_bills',
            sa.Column('retailer_id', sa.Uuid(), nullable=False, comment='用户ID'),
            sa.Column('bill_month', sa.String(length=7), nullable=False, comment='账单月份: 2026-07'),
            sa.Column('total_credit_used', sa.Integer(), nullable=False, comment='本期使用额度(分)'),
            sa.Column('total_repaid', sa.Integer(), nullable=False, comment='已还金额(分)'),
            sa.Column('status', sa.Enum('PENDING', 'PAID', 'OVERDUE', name='billstatus'), nullable=False),
            sa.Column('due_date', sa.String(length=10), nullable=True, comment='到期日'),
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.ForeignKeyConstraint(['retailer_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_credit_bills_retailer_id'), 'credit_bills', ['retailer_id'], unique=False)

    # --- knowledge_entries ---
    if not _has_table('knowledge_entries'):
        op.create_table(
            'knowledge_entries',
            sa.Column('source_type', sa.String(length=50), nullable=False, comment='来源: product|manual|faq|conversation'),
            sa.Column('source_id', sa.Uuid(), nullable=True, comment='关联商品ID'),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('content', sa.Text(), nullable=False, comment='知识内容（原始文本，用于全文搜索）'),
            sa.Column('embedding', sa.JSON(), nullable=True, comment='向量嵌入(1536维)，JSON存储兼容SQLite'),
            sa.Column('metadata', sa.JSON(), nullable=True, comment='元数据: 适龄、品类、认证等'),
            sa.Column('weight', sa.Float(), nullable=False, comment='权重（学习机制调整）'),
            sa.Column('status', sa.String(length=20), nullable=False, comment='active|deprecated'),
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.ForeignKeyConstraint(['source_id'], ['products.id'], ),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade() -> None:
    bind = op.get_bind()

    if _has_table('knowledge_entries'):
        op.drop_table('knowledge_entries')

    if _has_table('credit_bills'):
        op.drop_index(op.f('ix_credit_bills_retailer_id'), table_name='credit_bills')
        op.drop_table('credit_bills')

    if _has_table('promotions'):
        op.drop_table('promotions')

    # PostgreSQL 上 sa.Enum 会独立建类型，drop_table 不会带走它。
    # 不清理的话，重跑 upgrade head 会因为类型已存在而失败。
    # SQLite 没有原生枚举类型，跳过。
    if bind.dialect.name == 'postgresql':
        sa.Enum(name='promotiontype').drop(bind, checkfirst=True)
        sa.Enum(name='billstatus').drop(bind, checkfirst=True)
```

- [ ] **Step 4: 跑测试，确认通过**

```bash
cd backend && venv/Scripts/python -m pytest tests/test_migration_coverage.py -v
```

预期：三个测试全 **PASS**。

- [ ] **Step 4b: 证明列级守卫真的会失败（**不要跳过**）**

一个从不失败的守卫测试等于没有。刚才它在 Step 2 是通过的，本步必须亲自证明它有牙齿：

1. 在 `alembic/versions/e5f6a7b8c9d0_add_promotion_bill_knowledge.py` 里，把 `promotions` 的
   `sa.Column('is_active', sa.Boolean(), nullable=False)` 这一行**临时注释掉**；
2. 跑 `venv/Scripts/python -m pytest tests/test_migration_coverage.py -v`，确认
   `test_migration_columns_match_models` **FAIL**，且消息形如
   `promotions: 迁移少了这些列 -> ['is_active']`；
3. 恢复那一行，再跑一次确认回到全 PASS。

如果按第 1 步改完它仍然通过，说明 AST 解析没匹配到列——**守卫是坏的，必须修好再继续**，
后面所有「列对得上」的结论都不成立。

- [ ] **Step 5: 跑全量后端测试，确认没有回归**

```bash
cd backend && venv/Scripts/python -m pytest -q
```

预期：**162 passed**（基线 159 + 本任务的 3 个新用例）。特别确认 `tests/test_promotions.py::test_list_promotions_empty` 仍然通过——它走 SQLite `create_all`，不经过迁移。

- [ ] **Step 6: 在真实 PostgreSQL 上验证 —— 本机推迟，留到服务器执行**

> **用户已裁决：本机不做这一步。** 这个环境的 Docker 守护进程没有运行，用户选择不在本机启动 Docker Desktop，
> 把真实 PG 的验证推迟到部署时在服务器上跑。**执行者不要启动 Docker，不要建容器，也不要卡在这一步**——
> 按 Step 7 提交即可，并在报告里明确写出「检查点 A/B/C 未在本机执行，已推迟到服务器」。
>
> 代价必须说清楚：**这一步没做，迁移就还没在真实 PostgreSQL 上验证过。** SQLite 走的是 `create_all`，
> 结构上碰不到迁移；本任务新加的 `test_migration_columns_match_models` 只能比对列名与可空性，
> **验不了**枚举类型是否真的建出来、downgrade 是否清理干净枚举类型、表已存在时是否会抛 `DuplicateTable`。
> 这三个正是下面检查点 A/B/C 的靶子，最终交付时必须向用户单独重申。
>
> 部署时按下面的命令序列补做。

启动一个干净的 PostgreSQL：

```bash
cd backend
docker run -d --rm --name hxmall-pgtest \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=hxmall \
  -p 55432:5432 pgvector/pgvector:pg16
```

**检查点 A —— 干净库上前滚：**

```bash
cd backend
DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:55432/hxmall' alembic upgrade head
DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:55432/hxmall' \
  python -c "
import asyncio, asyncpg
async def main():
    c = await asyncpg.connect('postgresql://postgres:postgres@localhost:55432/hxmall')
    rows = await c.fetch(\"select tablename from pg_tables where schemaname='public' order by 1\")
    names = {r['tablename'] for r in rows}
    for t in ('promotions', 'credit_bills', 'knowledge_entries'):
        assert t in names, f'缺表: {t}'
    types = await c.fetch(\"select typname from pg_type where typname in ('promotiontype','billstatus')\")
    assert {r['typname'] for r in types} == {'promotiontype', 'billstatus'}, '缺枚举类型'
    print('OK 三张表 + 两个枚举类型都在')
    await c.close()
asyncio.run(main())
"
```

预期：输出 `OK 三张表 + 两个枚举类型都在`。

**检查点 B —— 回滚后再前滚（Review Focus #2）：**

```bash
cd backend
export DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:55432/hxmall'
alembic downgrade -1
alembic upgrade head
```

预期：两条命令都成功，无报错。这里最容易踩的是 PostgreSQL 枚举类型残留——`downgrade` 里那两行 `sa.Enum(...).drop()` 就是为了它。

**检查点 C —— 表已存在时仍能前滚（Review Focus #1）：**

```bash
cd backend
export DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:55432/hxmall'
alembic downgrade base
python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.models import Base
async def main():
    e = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:55432/hxmall')
    async with e.begin() as c:
        await c.run_sync(Base.metadata.create_all)
    await e.dispose()
asyncio.run(main())
"
alembic upgrade head
```

预期：`upgrade head` **成功**（不是 `DuplicateTableError`）。这正是 `_has_table()` 守卫要挡住的场景——没有它，这条命令会失败并中断部署。

**检查点 D —— 类型残留但表不存在时仍能前滚（Task 1 评审提出的边界场景）：**

检查点 C 只覆盖「表已存在」。还有一种半途失败会留下更脏的现场：某次 `upgrade` 在 `CREATE TYPE` 成功之后、
`CREATE TABLE` 之前中断（或建表语句报错），于是 `pg_type` 里留下了 `promotiontype` / `billstatus`，
而表并不存在。此时 `_has_table()` 守卫**不会**触发（它只看表），`op.create_table` 里的 `CREATE TYPE`
就会抛 `DuplicateObject`。

```bash
cd backend
export DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:55432/hxmall'
alembic downgrade base
python -c "
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
async def main():
    e = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:55432/hxmall')
    async with e.begin() as c:
        await c.execute(text('CREATE TYPE promotiontype AS ENUM (\'FULL_REDUCTION\',\'DISCOUNT\',\'FLASH_SALE\')'))
        await c.execute(text('CREATE TYPE billstatus AS ENUM (\'PENDING\',\'PAID\',\'OVERDUE\')'))
    await e.dispose()
asyncio.run(main())
"
alembic upgrade head
```

预期与处置：**这条很可能失败**（`DuplicateObject: type "promotiontype" already exists`）。计划**故意没有**
在 `upgrade` 里加 `DROP TYPE` 兜底——在升级路径里放 DROP 比这个边界场景本身更危险，而这是运维手工收拾
一次就能恢复的场景。真在服务器上遇到时，执行 `DROP TYPE IF EXISTS promotiontype, billstatus;` 再重跑
`upgrade head` 即可，并把这个观察记进交付报告。**不要为此改迁移代码。**

收尾：

```bash
docker stop hxmall-pgtest
```

- [ ] **Step 7: 提交**

```bash
cd backend
git add alembic/versions/e5f6a7b8c9d0_add_promotion_bill_knowledge.py tests/test_migration_coverage.py
git commit -m "$(cat <<'EOF'
fix(db): 补建 promotions/credit_bills/knowledge_entries 三张表

模型定义了 14 张表，迁移只建了 11 张。promotions 缺失导致
GET /promotions/active 在生产上 500（UndefinedTableError）。
deploy-prod.sh 确实在跑 alembic upgrade head，但迁移文件根本没写，
所以重跑修不好。

同时加一条守卫测试：比对 Base.metadata 与迁移源码里 create_table
的表名。现有测试走 create_all，结构上看不见这类漂移。

迁移对「表已存在」做了守卫，避免在有残留表的环境上抛
DuplicateTable 中断部署；downgrade 会清理 PostgreSQL 枚举类型。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: 案例筛选契约对齐——标签接口与 `style` 参数名

Spec §9 B2 实测两处漂移，都在案例 tab 上：

1. 前端 `pages/cases/index.vue:105` 调 `/cases/tags/styles` 和 `/cases/tags/categories`。后端只有 `/cases/tags`，这两个路径多一段，**没有任何路由能匹配，返回 404**（不是被 `/{case_id}` 捕获——`/{case_id}` 只吃一段路径）。`Promise.all` 直接 reject，筛选器永远只有「全部」。
2. 前端发 `style_tag=`，后端读的是 `style=`（`app/api/cases.py:36`）。多余的查询参数 FastAPI 直接忽略——**风格筛选静默失效**，不报错，只是筛了等于没筛。`category_tag` 两边一致，是好的。

后端 `/cases/tags` 已存在且返回正确形状（`app/api/cases.py:71-95`），**本任务不改后端**。

**已知的第三处漂移，本任务不修：** `list_cases`（`app/api/cases.py:34-40`）只接受 `page` / `page_size` / `style` / `area` / `category_tag` 五个参数，**没有 `keyword`**。而 `pages/cases/index.vue:128` 会发 `params.keyword` —— 和 `style_tag` 同期，被 FastAPI 静默忽略，案例页的搜索框**搜了等于没搜**。

之所以留着不修：修它必须改后端（加 `keyword` 参数 + `title`/`description` 的 `ilike` 查询），那是本计划的 §9 范围之外。本任务把 `params.keyword` 原样保留，是为了不把一次「契约对齐」变成一次静默的功能删除。**这是一处真实且已知的缺陷，不是本任务引入的**，最终交付时要单独向用户报出来。

**Files:**
- Modify: `miniapp/src/api/cases.ts`
- Modify: `miniapp/src/pages/cases/index.vue:82`（import）、`:104-112`（`loadTags`）、`:131-133`（params 拼装）
- Test: `miniapp/src/api/__tests__/cases.test.ts`

**Interfaces:**
- Consumes: 后端 `GET /cases/tags` → `{ category_tags: string[], style_tags: string[], area_ranges: string[] }`；`GET /cases` 的筛选参数为 `style` / `area` / `category_tag`（**没有 `keyword`**，见下方「已知的第三处漂移」）
- Produces:
  - `getCaseTags(): Promise<{ data: CaseTags }>`，`interface CaseTags { category_tags: string[]; style_tags: string[]; area_ranges: string[] }`
  - `CaseListParams` 的 `style_tag?: string` 改为 `style?: string`（`category_tag` / `keyword` / `page` / `page_size` 不变）

- [ ] **Step 1: 写失败测试**

创建 `miniapp/src/api/__tests__/cases.test.ts`。这些断言锁的是 URL 和查询参数——正是漂移发生的地方。

```ts
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../request', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), del: vi.fn() },
}))

import http from '../request'
import { getCaseList, getCaseTags } from '../cases'

const mockGet = vi.mocked(http.get)

describe('案例接口契约', () => {
  beforeEach(() => {
    mockGet.mockReset()
    mockGet.mockResolvedValue({ data: {} } as any)
  })

  it('标签接口打在后端真实存在的 /cases/tags 上', async () => {
    await getCaseTags()
    // 用 mock.calls[0][0] 而不是 toHaveBeenCalledWith('/cases/tags', undefined)：
    // getCaseTags() 只传一个实参，记录下来的 args 是 ['/cases/tags']（长度 1），
    // 和期望的 ['/cases/tags', undefined]（长度 2）长度不等，匹配不上。
    expect(mockGet.mock.calls[0][0]).toBe('/cases/tags')
    expect(mockGet.mock.calls[0]).toHaveLength(1)
  })

  it('风格筛选参数名是 style，不是 style_tag', async () => {
    await getCaseList({ style: 'ins风' })
    const [url, params] = mockGet.mock.calls[0]
    expect(url).toBe('/cases')
    expect(params).toMatchObject({ style: 'ins风' })
    expect(params).not.toHaveProperty('style_tag')
  })

  it('类型筛选参数名是 category_tag', async () => {
    await getCaseList({ category_tag: '儿童房' })
    const [, params] = mockGet.mock.calls[0]
    expect(params).toMatchObject({ category_tag: '儿童房' })
  })

  it('不传筛选条件时不带多余的空参数', async () => {
    await getCaseList({ page: 1, page_size: 20 })
    const [, params] = mockGet.mock.calls[0]
    expect(params).toEqual({ page: 1, page_size: 20 })
  })
})
```

- [ ] **Step 2: 跑测试，确认失败**

```bash
cd miniapp && npx vitest run src/api/__tests__/cases.test.ts
```

预期：**FAIL**。
- 因为 `getCaseTags` 尚未导出，本步先在导入处报 `does not provide an export named 'getCaseTags'`（整个文件收集失败）。这是 TDD 的正确起点。
- 修好导出之后，第二、四个用例才会真正跑起来：`style_tag` 还在 → `not.toHaveProperty('style_tag')` 失败；`style` 不存在 → `toMatchObject({ style: 'ins风' })` 失败。
- 第一个用例（URL 断言）要等下面的 Step 3 把 `getCaseTags` 真正指向 `/cases/tags` 才成立，本步它是被导入错误连带打断的。

- [ ] **Step 3: 改 `api/cases.ts`**

把 `getStyleTags` / `getCategoryTags` 换成一个 `getCaseTags`，并把 `style_tag` 改成 `style`：

```ts
import http from './request'

export interface DesignCase {
  id: string
  title: string
  description: string | null
  images: string[]
  category_tags: string[]
  style_tags: string[]
  store_area_range: string | null
  is_featured: boolean
  created_at: string | null
}

export interface CaseListParams {
  page?: number
  page_size?: number
  style?: string
  area?: string
  category_tag?: string
  keyword?: string
}

export interface CaseListResult {
  list: DesignCase[]
  total: number
  page: number
  page_size: number
}

/** GET /cases/tags 的返回形状，与后端 app/api/cases.py:list_tags 一致 */
export interface CaseTags {
  category_tags: string[]
  style_tags: string[]
  area_ranges: string[]
}

// Get case list
export function getCaseList(params: CaseListParams): Promise<{ data: CaseListResult }> {
  return http.get<CaseListResult>('/cases', params)
}

// Get case detail
export function getCaseDetail(id: string): Promise<{ data: DesignCase }> {
  return http.get<DesignCase>(`/cases/${id}`)
}

// Get all filter tags in one call
export function getCaseTags(): Promise<{ data: CaseTags }> {
  return http.get<CaseTags>('/cases/tags')
}
```

改动说明，两条都必须做：

- `DesignCase` 的字段被裁到**后端 `CaseListOut` / `CaseOut` 实际返回的集合**（`app/schemas/case.py:44-63`）。原接口声明的 `cover_image`、`designer_name`、`designer_avatar`、`used_products`、`view_count`、`like_count`、`is_liked` 后端一个都不返回——它们此前渲染出来全是 `undefined`。`id` 从 `number` 改成 `string`：后端是 UUID。

  一点必须知情的取舍：`description` 只在 `CaseOut`（详情）里返回，`CaseListOut`（列表）**不返回**。这里保留 `description: string | null` 是为了让详情页能用同一个类型；代价是列表项取它会是 `undefined` 而不是 `null`。列表页本来也不渲染它，所以不构成问题——但**不要**因为看到类型里有 `description` 就想在列表卡片上用它。
- `likeCase` 本步先保留，Task 3 删。

- [ ] **Step 4: 改 `pages/cases/index.vue`**

三处。import 行（`:82`）：

```ts
import { getCaseList, getCaseTags } from '../../api/cases'
```

`loadTags`（`:104-112`）——两次请求合并成一次，并且失败时**静默降级**（Review Focus #4）：

```ts
async function loadTags() {
  try {
    const res = await getCaseTags()
    styleTags.value = res.data?.style_tags || []
    categoryTags.value = res.data?.category_tags || []
  } catch {
    // 标签是非关键路径。接口失败或后端仍是旧版本时，
    // 保持两个数组为空 —— 筛选器只剩「全部风格」/「全部类型」，页面照常可用。
  }
}
```

params 拼装（`:131-133`）：

```ts
    if (activeStyleTag.value) params.style = activeStyleTag.value
    if (activeCategoryTag.value) params.category_tag = activeCategoryTag.value
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
```

- [ ] **Step 5: 跑测试，确认通过**

```bash
cd miniapp && npx vitest run src/api/__tests__/cases.test.ts
```

预期：4 个用例全 **PASS**。

- [ ] **Step 6: 跑全量前端测试，确认没有回归**

```bash
cd miniapp && npm test
```

预期：**58 passed**（基线实测 54 + 本任务的 4 个）。基线是 5 个测试文件、54 个用例，改动前 `npx vue-tsc --noEmit` 也是干净的 —— 所以这里没有任何「本来就有错」可以当借口。

> **注意：这一步之后 `npx vue-tsc --noEmit` 会报错，这是预期的。** Step 3 把 `DesignCase` 裁小之后，`pages/cases/detail.vue` 里引用 `designer_name` / `view_count` / `like_count` / `used_products` / `is_liked` 的地方全成了类型错误。**本步不要跑 vue-tsc，也不要顺手去改 `detail.vue`** —— 那是 Task 3 的范围，它会把消费端一次清干净。vitest 只收集 `src/{api,utils,stores}/__tests__/`，不碰 `.vue`，所以本步的全绿是真实的。
>
> 换句话说：**Task 2 和 Task 3 之间仓库的 `vue-tsc` 是红的，这是设计好的中间态。** 两个任务挨着做，中间不要插入别的改动。

- [ ] **Step 7: 在真实 PostgreSQL 上手工验证筛选 —— 本机推迟，留到服务器执行**

> **用户已裁决：本机不做这一步**（Docker 守护进程没运行，本机不启动 Docker Desktop）。
> **执行者不要卡在这一步**，也不要为了「能验证」去改 `app/api/cases.py` —— 本任务不改后端。
> 提交即可，并在报告里写明「风格/类型筛选的真实 PG 行为未在本机验证，已推迟到服务器」。
>
> 代价：`JSON.contains`（`app/api/cases.py:46,52`）在 PG 与 SQLite 上行为不同，**本地全绿不等于线上能筛**。
> 参数名改对是本任务能保证的；「改对之后筛得动」只有服务器上的真实 PG 能证明。最终交付时要重申。

Spec §11 记着：后端测试跑 SQLite，生产是 PG，而案例标签筛选用 `JSON.contains`（`app/api/cases.py:46,52`），两库行为有差异。**测试全绿不等于线上能筛。**

依赖 Task 5 的种子数据。若 Task 5 尚未完成，先手工插一条案例：

```bash
cd backend
curl -s -X POST 'http://localhost:8000/api/v1/cases' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"title":"筛选用例","images":["https://example.com/a.jpg"],
       "category_tags":["儿童房"],"style_tags":["ins风"],
       "store_area_range":"50-100㎡","status":"published"}'
```

然后逐条确认：

```bash
# 1. 标签接口在真实 PG 上返回三个键（Review Focus #5）
curl -s "http://localhost:8000/api/v1/cases/tags" | jq '.data | keys'
# 预期: ["area_ranges","category_tags","style_tags"]  —— 不能是 500，也不能缺键

# 2. 风格筛选真的筛掉了（app/api/cases.py:46 的 JSON.contains）
curl -s "http://localhost:8000/api/v1/cases?style=ins风" | jq '.data.total'
curl -s "http://localhost:8000/api/v1/cases?style=不存在的风格" | jq '.data.total'
# 预期: 前者 >= 1，后者 == 0。若后者也 >= 1，说明 JSON.contains 在 PG 上没生效

# 3. 类型筛选
curl -s "http://localhost:8000/api/v1/cases?category_tag=儿童房" | jq '.data.total'
# 预期: >= 1
```

第 2 条是关键。前端改对参数名之后，筛选能不能真的生效取决于 `JSON.contains` 在 PG 上的行为——这是 SQLite 测试覆盖不到的那一段。

- [ ] **Step 8: 提交**

```bash
git add miniapp/src/api/cases.ts miniapp/src/pages/cases/index.vue miniapp/src/api/__tests__/cases.test.ts
git commit -m "$(cat <<'EOF'
fix(miniapp): 案例筛选对齐后端真实契约

两处漂移：
1. 调 /cases/tags/styles 和 /cases/tags/categories —— 后端只有
   /cases/tags，这两个路径没有任何路由能匹配（/{case_id} 只吃
   一段路径），返回 404，筛选器永远只有「全部」。改为一次调
   /cases/tags 取三个标签数组。
2. 发 style_tag=，后端读的是 style= —— 多余查询参数被 FastAPI
   静默忽略，风格筛选一直是筛了等于没筛。改名对齐。

同时把 DesignCase 裁到后端实际返回的字段集：原接口声明的
cover_image/designer_name/used_products/view_count/like_count/
is_liked 后端一个都不返回，此前渲染出来全是 undefined。
id 由 number 改为 string（后端是 UUID）。

标签接口失败时静默降级为空数组，不阻塞页面。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: 案例详情：清理幻影字段 UI，并去掉点赞

两件事合并成一个任务，因为它们改的是同一个文件、同一个根因，且**必须一起做完**：

- **去掉点赞**（Spec §2 #16）：后端没有点赞接口（全库搜不到 `like`），`pages/cases/detail.vue:148` 单方面在调 `likeCase`。已定：前端去掉，含调用与 UI。理由——B2B 批发场景点赞价值低，补后端要新建关系表 + 迁移 + 接口 + 测试，为一个弱需求抬高成本；案例「收藏」已有。
- **清理幻影字段 UI**：Task 2 把 `DesignCase` 裁到了后端 `CaseListOut` 实际返回的字段集，于是 `detail.vue` 里所有引用被删字段的地方都成了类型错误。**这些地方 Task 3 之外的任何任务都不会碰**——漏掉这一步，最终 `vue-tsc --noEmit` 一定报错，验收过不了。

`pages/cases/detail.vue` 里引用到的幻影字段，共 5 个：

| 字段 | 位置 | 处理 |
|---|---|---|
| `designer_name` / `designer_avatar` | 32-40 行的「设计师」行 | 整块删 |
| `view_count` | 44-47 行的浏览数 | 删 |
| `like_count` | 48-51 行的点赞按钮 | 整块删（连同点赞功能） |
| `used_products` | 65-81 行的「用到的商品」区 | 整块删 |
| `is_liked` | 112、120、149 行 | 删（随点赞一起） |

**另有一处与 id 类型相关的错误，也必须在本任务一并修掉**（它是 Task 2 改 `getCaseDetail(id: string)` 之后 `vue-tsc` 会逼出来的，但根子是一个真实的运行时 bug，不只是类型问题）：

| 位置 | 现状 | 处理 |
|---|---|---|
| `loadCase(id: number)` | 114 行 | 改成 `loadCase(id: string)` |
| `onLoad` 里的 `Number(options?.id)` | 129 行 | 删掉 `Number(...)`，直接把 `options?.id` 当字符串用 |

后端 `cases.id` 是 **UUID**（`app/schemas/case.py:46` 的 `id: UUID`），而 `pages/cases/index.vue:178` 跳转时传的就是这个 UUID 字符串。`Number("3f2b…-…")` 得到 `NaN`，`if (id)` 判假，页面直接落到「案例ID无效」——**案例详情页对真实数据是打不开的**。这个 bug 一直存在，只是被幻影字段的类型错误盖住了。

**Files:**
- Modify: `miniapp/src/api/cases.ts`（删 `likeCase`）
- Modify: `miniapp/src/pages/cases/detail.vue`（`likeCase` import、`isLiked` state、`toggleLike`、以及上表五个字段的全部引用）
- Test: `miniapp/src/api/__tests__/cases.test.ts`（追加）

**Interfaces:**
- Consumes: 无
- Produces: 从 `api/cases.ts` 移除 `likeCase` 导出。`DesignCase` 里已无 `like_count` / `is_liked` / `designer_*` / `view_count` / `used_products`（Task 2 Step 3 已裁掉）

- [ ] **Step 0: 先看一遍当前有哪些类型错误**

Task 2 刚把 `DesignCase` 裁小，此刻 `vue-tsc` 应该已经在报 `detail.vue` 的错误了。先跑一次，把清单拿在手里：

```bash
cd miniapp && npx vue-tsc --noEmit
```

预期：报出 `detail.vue` 里若干 `Property 'xxx' does not exist on type 'DesignCase'`，涉及的属性名基本就是上表那 5 个。**以编译器实际列出的为准**——如果多出别的属性，一并按同样的方式处理（说明 Task 2 裁字段时裁掉了一个这里还在用的）。这个任务做完，这条命令必须干净。

- [ ] **Step 1: 追写失败测试**

在 `miniapp/src/api/__tests__/cases.test.ts` 末尾追加：

```ts
it('不再导出 likeCase —— 后端没有这个接口', async () => {
  const mod = await import('../cases')
  expect(mod).not.toHaveProperty('likeCase')
})
```

- [ ] **Step 2: 跑测试，确认失败**

```bash
cd miniapp && npx vitest run src/api/__tests__/cases.test.ts
```

预期：**FAIL** —— `expected { … } not to have property "likeCase"`。

- [ ] **Step 3: 删掉 `api/cases.ts` 里的 `likeCase`**

删除这段（位于 `getCaseDetail` 与 `getCaseTags` 之间）：

```ts
// Like a case
export function likeCase(id: number): Promise<{ data: { is_liked: boolean; like_count: number } }> {
  return http.post(`/cases/${id}/like`)
}
```

- [ ] **Step 4: 清理 `pages/cases/detail.vue`**

**① 模板里的四块 UI，整块删除。**

- 设计师行（约 32-42 行）——`v-if="caseData.designer_name"` 那个 `<view class="designer-row">`
- 浏览数（约 44-47 行）——渲染 `caseData.view_count` 的那段
- 点赞按钮（约 48-53 行）——含 `caseData.like_count` 的那个可点击块，连同它的 `@tap="toggleLike"`
- 「用到的商品」区（约 65-85 行）——`v-if="caseData.used_products && caseData.used_products.length"` 的整个 `<view class="products-section">`

删完后：这几个块的外层容器若只剩一个子元素，把容器一并简化；**不要留下空的 flex 容器或空的分隔线**。统计条那一行如果只剩标签，把它的布局调成单行左对齐。

**② 脚本里的四处删除。**

import（约 105 行）改成：

```ts
import { getCaseDetail } from '../../api/cases'
```

state（约 113 行）—— 整行删除：

```ts
const isLiked = ref(false)
```

`loadCase` 里（约 120 行）—— 整行删除：

```ts
    isLiked.value = res.data.is_liked
```

整个 `toggleLike` 函数（约 146-157 行）—— 整段删除：

```ts
async function toggleLike() {
  if (!caseData.value) return
  try {
    const res = await likeCase(caseData.value.id)
    isLiked.value = res.data.is_liked
    caseData.value.like_count = res.data.like_count
    showSuccess(isLiked.value ? '已收藏' : '已取消收藏')
  } catch (err: any) {
    showError('操作失败')
  }
}
```

**③ 清掉因删块而产生的孤儿。** 这一步**不能指望 `vue-tsc` 兜底**——`miniapp/tsconfig.json` 里没有开 `noUnusedLocals`，未使用的 import 和没人调用的函数它一律不报。漏了这一步，本任务的验收（vue-tsc 干净）照样通过，但会在文件里留下死代码。逐个查实过的结论如下（行号是 HEAD `8397c58` 时的）：

- `:105` → `import { getCaseDetail } from '../../api/cases'`（去掉 `likeCase`）
- `:107` `import { formatPrice, showSuccess, showError } from '../../utils/index'` **只保留 `showSuccess`**：
  - `formatPrice` 唯一的用处是 `:77`（被删的商品区里的商品价格）
  - `showError` 唯一的用处是 `:153`（被删的 `toggleLike` 里的 catch）
  - `showSuccess` 还有 `:162`（`handleContact` 在用），**必须保留**
- 删掉整个 `goToProduct` 函数（`:157-159`）——它唯一的调用点 `:73` 就在被删的商品区里
- `previewImage`（`:22` 的 swiper 在用）与 `handleContact`（`:93` 在用）**不动**

改完后再 grep 一次这四个名字，确认上面的结论在你改完之后仍然成立（`grep -n "goToProduct\|formatPrice\|showError\|showSuccess" miniapp/src/pages/cases/detail.vue`）：预期的剩余引用只有 `showSuccess` 的 import 与 `:162`。

**⑤ 清掉只服务于被删块儿的样式。** 四个 UI 块删掉后，`<style>` 里给它们的规则没人再引用。删除前先对每个类名 grep 一次模板，**确认它在模板里已经完全不出现**再删；有任何一处仍在用就保留。重点看 `.designer-row` / `.designer-name` / `.designer-avatar` / 点赞按钮相关（`.like-*`、`.btn-like`）/ `.products-section` 及其子类 / `.product-price`。**拿不准的保留**——死 CSS 是瑕疵，删错共享类名是 bug。

**④ 修掉 id 的 number/string 错配。**

```ts
async function loadCase(id: string) {
```

```ts
onLoad((options: any) => {
  const id = options?.id
  if (id) {
    loadCase(id)
  } else {
    errorMsg.value = '案例ID无效'
  }
})
```

`Number()` 必须去掉，不是可选的美化：案例 id 是 UUID 字符串，`Number()` 会得到 `NaN` 并让详情页永远显示「案例ID无效」。`goToProduct(id: number)` 是另一个函数的参数（商品 id），**不要**一起改。

- [ ] **Step 5: 跑测试与类型检查，确认通过**

```bash
cd miniapp && npx vitest run src/api/__tests__/cases.test.ts && npx vue-tsc --noEmit
```

预期：vitest 全 **PASS**；`vue-tsc` **无输出**（Step 0 列出的错误全部消失）。

`vue-tsc` 是这个任务真正的验收手段——`pages/cases/detail.vue` 没有测试覆盖，漏删任何一个幻影字段的引用，只有类型检查抓得住。**这一步不干净就不算做完。**

**但 `vue-tsc` 干净不等于做完了。** 它保证的是「类型对得上」，不是「没有留下残骸」——`noUnusedLocals` 没开，所以未使用的 import 和没人调用的函数它都放行。收起这一步之前，再确认 `grep -n "goToProduct\|formatPrice\|showError" miniapp/src/pages/cases/detail.vue` **只剩 `showSuccess` 之外的零命中**（Step ④ 的收尾清单）。

- [ ] **Step 6: 跑全量前端测试**

```bash
cd miniapp && npm test
```

预期：**60 passed**（Task 2 之后的 59 + 本任务追加的 1 个）。

- [ ] **Step 7: 提交**

```bash
git add miniapp/src/api/cases.ts miniapp/src/pages/cases/detail.vue miniapp/src/api/__tests__/cases.test.ts
git commit -m "$(cat <<'EOF'
fix(miniapp): 案例详情清掉幻影字段 UI，并去掉点赞

两件事同源：后端 CaseListOut 不返回这些字段，前端照着想象中的
接口写，渲染出来全是 undefined。

- 去掉点赞：后端不存在 /cases/{id}/like，点一次报一次错。
  B2B 批发场景点赞价值低，补后端要新建关系表+迁移+接口+测试，
  为一个弱需求抬高成本；案例「收藏」已有，功能不缺。
- 去掉设计师行、浏览数、「用到的商品」区：designer_name /
  designer_avatar / view_count / used_products 后端一个都不返回。

DesignCase 类型在上一提交已裁到真实字段集，本提交清掉消费端。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: 退出登录改为清本地 token

Spec §2 #17：后端没有 `POST /auth/logout`，`api/auth.ts` 里的 `logout()` 导出**没有任何调用方**——两个使用处（`pages/mine/index.vue:187`、`pages/mine/settings/index.vue:51`）调的都是 `userStore.logout()`，而 store 的实现（`stores/user.ts:112-121`）本来就只清本地状态、不发请求。

所以这是一次纯粹的清理：删掉一个坏掉的、没人用的导出。JWT 无状态，后端无可做（除非上 token 黑名单，那是额外基建）。

**Files:**
- Modify: `miniapp/src/api/auth.ts`（删 `logout`）
- Test: `miniapp/src/api/__tests__/auth.test.ts`

**Interfaces:**
- Consumes: `stores/user.ts` 的 `logout()`（已存在，不改）
- Produces: 从 `api/auth.ts` 移除 `logout` 导出

- [ ] **Step 1: 写失败测试**

创建 `miniapp/src/api/__tests__/auth.test.ts`：

```ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('../request', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), del: vi.fn() },
}))

import * as authApi from '../auth'
import { useUserStore } from '../../stores/user'

// 与 stores/__tests__/user.test.ts 同一套装配：store 的 setup 会碰 uni 的存储 API，
// 而 useUserStore() 没有 active Pinia 时会直接抛 getActivePinia()。
const uniMock = {
  getStorageSync: () => '',
  setStorageSync: () => {},
  removeStorageSync: () => {},
  login: (opts: any) => opts?.success?.({ code: 'dev_b2_test' }),
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.stubGlobal('uni', uniMock)
})

describe('auth 接口契约', () => {
  it('不再导出 logout —— 后端没有 POST /auth/logout', () => {
    expect(authApi).not.toHaveProperty('logout')
  })

  it('登出是纯本地行为，靠 store 的 logout() 完成', () => {
    // 这一条是「别删错」的守卫：本任务删的是 api/auth.ts 的同名导出，
    // 不是 store 里这个。两者同名，删错任何一处页面就登不出去。
    expect(typeof useUserStore().logout).toBe('function')
  })
})
```

- [ ] **Step 2: 跑测试，确认失败**

```bash
cd miniapp && npx vitest run src/api/__tests__/auth.test.ts
```

预期：第一个用例 **FAIL** —— `expected { … } not to have property "logout"`。第二个应当 PASS。

上面 Step 1 的代码里已经带了 `setActivePinia(createPinia())` 与 `uni` 的 stub，这正是
`stores/__tests__/user.test.ts:19-24` 在用的那套装配（顶层 import store 也安全——该文件就是这么写的）。
若第二个用例仍然报 Pinia 或 `uni is not defined`，**停下来把完整报错贴进报告**，不要自己换一套写法。

- [ ] **Step 3: 删掉 `api/auth.ts` 里的 `logout`**

删除这一行：

```ts
export const logout = () => http.post('/auth/logout')
```

- [ ] **Step 4: 跑测试与类型检查，确认通过**

```bash
cd miniapp && npx vitest run src/api/__tests__/auth.test.ts && npx vue-tsc --noEmit
```

预期：全 **PASS**，类型检查干净。

`vue-tsc` 在这里是必需品而不是保险——它确认「没有任何调用方」这个前提还成立。如果它报了 `Cannot find name 'logout'`，说明有调用方漏了，回去改调用方而不是恢复导出。

- [ ] **Step 5: 跑全量前端测试**

```bash
cd miniapp && npm test
```

预期：**62 passed**（Task 3 之后的 60 + 本任务的 2 个）。

- [ ] **Step 6: 提交**

```bash
git add miniapp/src/api/auth.ts miniapp/src/api/__tests__/auth.test.ts
git commit -m "$(cat <<'EOF'
fix(miniapp): 删掉指向不存在接口的 logout 导出

后端没有 POST /auth/logout。这个导出没有任何调用方——
mine/index.vue 和 mine/settings/index.vue 调的都是
userStore.logout()，而 store 的实现本来就只清本地 token。
JWT 无状态，后端无可做。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: 幂等种子脚本

Spec §1 实测：商品 total = 0、分类 = []、案例 total = 0。全库唯一的建数据脚本是 `deploy/create_admin.py`（建一个管理员），不灌任何商品／案例／促销。5 个 tab 页目前没有任何内容可显示。

幂等策略用**「存在即跳过」而非「先删后插」**——先删后插会抹掉运维手工改过的数据。

**Files:**
- Create: `backend/scripts/__init__.py`
- Create: `backend/scripts/seed.py`
- Test: `backend/tests/test_seed.py`

**Interfaces:**
- Consumes: 模型 `Category`、`Product`、`ProductStatus`（`app/models/product.py`）、`DesignCase`（`app/models/case.py`）、`Promotion`、`PromotionType`（`app/models/promotion.py`）；`tests/conftest.py` 的 `db_session` fixture
- Produces: `scripts.seed.run_seed(db) -> dict[str, int]`（异步，返回各类新增条数）；`python -m scripts.seed` 可执行入口

- [ ] **Step 1: 写失败测试**

创建 `backend/tests/test_seed.py`。幂等性用**「半有半无」的中间状态**检验，不是空库跑两遍——后者太容易过关。

```python
"""种子脚本测试：幂等性与数据合法性。

每个用例都同时请求 `client` 和 `db_session` 两个 fixture —— 这不是多余的：
`db_session`（tests/conftest.py:78-83）只开一个 session，**不建表**；
真正跑 `Base.metadata.create_all` 的是 `client`（tests/conftest.py:56-58）。
现有测试无一例外都是 `(client, db_session)` 一起用，只写 `db_session`
会得到 `no such table: categories`。
"""
import pytest
from sqlalchemy import select, func

from scripts.seed import CATEGORIES, run_seed


async def _counts(db) -> dict[str, int]:
    from app.models.product import Category, Product
    from app.models.case import DesignCase
    from app.models.promotion import Promotion

    out = {}
    for name, model in (
        ("categories", Category),
        ("products", Product),
        ("cases", DesignCase),
        ("promotions", Promotion),
    ):
        out[name] = (await db.execute(select(func.count()).select_from(model))).scalar_one()
    return out


@pytest.mark.asyncio
async def test_seed_creates_data(client, db_session):
    written = await run_seed(db_session)
    await db_session.commit()

    counts = await _counts(db_session)
    assert counts["categories"] > 0
    assert counts["products"] > 0
    assert counts["cases"] > 0
    assert counts["promotions"] > 0
    assert sum(written.values()) > 0


@pytest.mark.asyncio
async def test_seed_is_idempotent(client, db_session):
    """空库连跑两遍不产生重复。"""
    await run_seed(db_session)
    await db_session.commit()
    first = await _counts(db_session)

    await run_seed(db_session)
    await db_session.commit()
    second = await _counts(db_session)

    assert first == second


@pytest.mark.asyncio
async def test_seed_is_idempotent_from_partial_state(client, db_session):
    """半有半无的中间状态：只建了分类，商品/案例/促销还没建。

    这才是幂等性的真实检验 —— 空库跑两遍很容易过，
    「分类在、商品不在」的状态最容易被「先查后插」写错。
    """
    from app.models.product import Category

    db_session.add(Category(name="婴童服饰", sort_order=1, status="active"))
    await db_session.commit()

    written = await run_seed(db_session)
    await db_session.commit()
    first = await _counts(db_session)

    # 种子里一级分类 + 全部子分类的总条数。从 CATEGORIES 算出来而不是写死，
    # 以后往种子里加分类，这条断言不会失效。
    expected_total = sum(1 + len(children) for _, _, children in CATEGORIES)

    # 预先存在的那条一级分类不能被重复插入 —— 这是本用例的核心
    dupes = (await db_session.execute(
        select(func.count()).select_from(Category).where(
            Category.name == "婴童服饰", Category.parent_id.is_(None)
        )
    )).scalar_one()
    assert dupes == 1, "预先存在的一级分类被重复插入了"

    # 总数 = 全部应建的条数（预置那条本来就在，所以总数不变）
    assert first["categories"] == expected_total
    # 其余三类照常建出来
    assert first["products"] > 0
    assert first["cases"] > 0
    assert first["promotions"] > 0
    # 新增只比全量少那一条预置的
    assert written["categories"] == expected_total - 1

    await run_seed(db_session)
    await db_session.commit()
    assert await _counts(db_session) == first


@pytest.mark.asyncio
async def test_seeded_products_have_valid_pricing(client, db_session):
    """每个商品的定价矩阵都要能被定价引擎用（qty 升序、有 normal 档）。"""
    from app.models.product import Product

    await run_seed(db_session)
    await db_session.commit()

    products = (await db_session.execute(select(Product))).scalars().all()
    assert products, "没有种子商品"
    for p in products:
        assert "normal" in p.pricing_rules, f"{p.name} 缺 normal 档"
        for level, tiers in p.pricing_rules.items():
            assert tiers, f"{p.name}/{level} 是空档"
            qtys = [t["qty"] for t in tiers]
            assert qtys == sorted(qtys), f"{p.name}/{level} 的 qty 不是升序"
            for t in tiers:
                assert t["qty"] > 0 and t["price"] > 0, f"{p.name}/{level} 有非法阶梯"


@pytest.mark.asyncio
async def test_seeded_promotions_are_currently_active(client, db_session):
    """品牌活动分区取的是 /promotions/active，种子促销必须落在有效期内。"""
    from datetime import datetime, timezone
    from app.models.promotion import Promotion

    await run_seed(db_session)
    await db_session.commit()

    now = datetime.now(timezone.utc)
    promos = (await db_session.execute(select(Promotion))).scalars().all()
    assert promos
    for p in promos:
        assert p.is_active, f"{p.title} 没启用"
        assert p.start_time <= now <= p.end_time, f"{p.title} 不在有效期内"
```

- [ ] **Step 2: 跑测试，确认失败**

```bash
cd backend && venv/Scripts/python -m pytest tests/test_seed.py -v
```

预期：**FAIL**，`ModuleNotFoundError: No module named 'scripts'`。

- [ ] **Step 3: 建 `scripts` 包**

```bash
cd backend && mkdir -p scripts && touch scripts/__init__.py
```

`scripts/` 目录当前**不存在**，所以 `mkdir -p` 不能省——直接 `touch scripts/__init__.py` 会报 `No such file or directory`。

`tests/__init__.py` 已存在，pytest 会把 `backend/` 加进 `sys.path`，所以 `import scripts.seed` 能解析。

- [ ] **Step 4: 写种子脚本**

创建 `backend/scripts/seed.py`。三类数据的幂等键都是**业务唯一键**（表上没有对应的唯一约束，所以靠「先查后跳过」保证）：分类按 `(name, parent_id)`、商品按 `name`、案例按 `title`、促销按 `title`。

```python
"""种子数据：分类、商品、案例、促销。

幂等 —— 所有写入都走 _get_or_create（按业务唯一键查询，存在即返回）。
重复执行不产生重复行，也不覆盖运维后续手工改过的数据。
不用「先删后插」：那会抹掉人工修改。

用法：
    cd backend && python -m scripts.seed
"""
import asyncio
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database import async_session_factory
from app.models.case import DesignCase
from app.models.product import Category, Product, ProductStatus
from app.models.promotion import Promotion, PromotionType


# ── 数据定义 ─────────────────────────────────────────────────────────────────

# (名称, 排序, 子分类)
CATEGORIES: list[tuple[str, int, list[str]]] = [
    ("婴童服饰", 1, ["连体衣", "外出服", "内衣套装"]),
    ("喂养用品", 2, ["奶瓶奶嘴", "辅食餐具", "消毒烘干"]),
    ("寝居出行", 3, ["婴儿床", "推车安全座椅", "床品寝具"]),
    ("洗护用品", 4, ["洗浴护理", "纸尿裤", "湿巾"]),
    ("玩具早教", 5, ["益智积木", "早教绘本", "户外玩具"]),
]

# 定价矩阵的键是小写等级值 normal/silver/gold（app/services/pricing.py:11）
def _tiers(base: float, min_qty: int = 10) -> dict:
    """按起批量生成三档等级价：等级越高单价越低，数量越大单价越低。"""
    return {
        "normal": [
            {"qty": min_qty, "price": round(base, 2)},
            {"qty": min_qty * 5, "price": round(base * 0.94, 2)},
            {"qty": min_qty * 20, "price": round(base * 0.88, 2)},
        ],
        "silver": [
            {"qty": min_qty, "price": round(base * 0.92, 2)},
            {"qty": min_qty * 5, "price": round(base * 0.86, 2)},
            {"qty": min_qty * 20, "price": round(base * 0.80, 2)},
        ],
        "gold": [
            {"qty": min_qty, "price": round(base * 0.85, 2)},
            {"qty": min_qty * 5, "price": round(base * 0.79, 2)},
            {"qty": min_qty * 20, "price": round(base * 0.72, 2)},
        ],
    }


# (分类名, 商品名, 适龄, 起批量, 基准价, 库存, 描述)
PRODUCTS: list[tuple[str, str, str, int, float, int, str]] = [
    ("连体衣", "纯棉长袖连体衣 新生儿爬服", "0-3岁", 10, 38.0, 5000, "精梳棉，四季通用，A 类婴幼儿标准"),
    ("连体衣", "冬季加厚夹棉连体衣", "0-3岁", 10, 68.0, 3000, "三层夹棉，保暖透气，包脚设计"),
    ("外出服", "婴儿外出抱衣套装", "0-3岁", 10, 88.0, 2000, "帽子+抱衣两件套，防风面料"),
    ("内衣套装", "儿童纯棉家居服两件套", "3-6岁", 20, 45.0, 4000, "40 支精梳棉，无骨缝制"),
    ("奶瓶奶嘴", "宽口径玻璃奶瓶 240ml", "0-3岁", 12, 42.0, 2600, "耐高温硼硅玻璃，防胀气奶嘴"),
    ("辅食餐具", "硅胶辅食碗勺套装", "0-3岁", 24, 16.0, 8000, "食品级硅胶，可蒸煮消毒"),
    ("消毒烘干", "紫外线奶瓶消毒柜", "0-3岁", 5, 320.0, 600, "18L，烘干+消毒二合一"),
    ("婴儿床", "实木多功能婴儿床", "0-3岁", 3, 260.0, 400, "新西兰松木，可改书桌，含护栏"),
    ("床品寝具", "婴儿床品七件套", "0-3岁", 10, 128.0, 1200, "A 类纯棉，含被芯枕芯床围"),
    ("推车安全座椅", "轻便折叠婴儿推车", "0-3岁", 4, 380.0, 300, "5.9kg 轻量，一键收车，可登机"),
    ("洗浴护理", "婴儿洗发沐浴二合一 500ml", "0-3岁", 24, 22.0, 6000, "无泪配方，弱酸性"),
    ("纸尿裤", "超薄透气纸尿裤 L 码", "0-3岁", 30, 58.0, 9000, "进口芯体，3 秒吸收"),
    ("湿巾", "婴儿手口湿巾 80 抽", "0-3岁", 60, 8.5, 20000, "纯水配方，无香精酒精"),
    ("益智积木", "大颗粒益智积木 80 粒", "3-6岁", 20, 52.0, 2500, "食品级 ABS，圆角无毛刺"),
    ("早教绘本", "启蒙认知绘本套装 20 册", "3-6岁", 30, 36.0, 3000, "硬壳撕不烂，环保大豆油墨"),
    ("户外玩具", "儿童三轮脚踏车", "3-6岁", 6, 168.0, 800, "加宽静音轮，可推可骑"),
]

# (标题, 描述, 分类标签, 风格标签, 面积, 排序, 精选)
CASES: list[tuple[str, str, list[str], list[str], str, int, bool]] = [
    ("北欧风儿童房整体方案", "0-3 岁婴幼儿房，含 12 件套柜体与睡眠区动线",
     ["儿童房"], ["ins风", "自然原木"], "50-100㎡", 100, True),
    ("蒙氏游戏区动线设计", "1-3 岁低龄安全动线，地面软包与低位收纳",
     ["游戏区"], ["ins风", "卡通童趣"], "50-100㎡", 90, True),
    ("连锁母婴生活馆标准店", "200㎡ 标准店型，商品区与体验区分区陈列",
     ["母婴生活馆"], ["简约现代"], "200㎡+", 80, True),
    ("婴童游泳馆空间方案", "恒温泳池区 + 家长等候区 + 更衣动线",
     ["婴童游泳馆"], ["简约现代"], "100-200㎡", 70, True),
    ("童趣儿童乐园主题店", "3-6 岁攀爬区与角色扮演区，全套软包防护",
     ["儿童乐园"], ["卡通童趣"], "200㎡+", 60, False),
    ("自然原木系亲子空间", "原木家具 + 绿植，亲子阅读与手作区",
     ["儿童房"], ["自然原木"], "50-100㎡", 50, False),
    ("社区母婴店改造案例", "80㎡ 老店翻新，动线重排后陈列面增加 40%",
     ["母婴生活馆"], ["简约现代"], "50-100㎡", 40, False),
    ("托育中心活动区设计", "分龄活动区 + 午睡区 + 配餐区一体化",
     ["儿童乐园"], ["ins风", "自然原木"], "200㎡+", 30, False),
]

# (标题, 类型, 规则)
PROMOTIONS: list[tuple[str, PromotionType, dict]] = [
    ("春季订货会 · 全场满减", PromotionType.FULL_REDUCTION,
     {"threshold": 500000, "reduce": 80000}),   # 满 5000 减 800（分）
    ("奶粉纸尿裤专享折扣", PromotionType.DISCOUNT,
     {"rate": 0.85}),                            # 85 折
    ("新品首发 · 连体衣限时价", PromotionType.FLASH_SALE,
     {"price": 3200, "limit_qty": 500}),         # 32 元 / 限 500 件
]


# ── 幂等写入 ─────────────────────────────────────────────────────────────────

async def _get_or_create_category(db, name: str, parent_id, sort_order: int) -> tuple[Category, bool]:
    stmt = select(Category).where(Category.name == name, Category.parent_id == parent_id)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        return existing, False
    cat = Category(name=name, parent_id=parent_id, sort_order=sort_order, status="active")
    db.add(cat)
    await db.flush()
    return cat, True


async def _get_or_create_product(db, data: dict) -> bool:
    existing = (await db.execute(
        select(Product).where(Product.name == data["name"])
    )).scalar_one_or_none()
    if existing:
        return False
    db.add(Product(**data))
    await db.flush()
    return True


async def _get_or_create_case(db, data: dict) -> bool:
    existing = (await db.execute(
        select(DesignCase).where(DesignCase.title == data["title"])
    )).scalar_one_or_none()
    if existing:
        return False
    db.add(DesignCase(**data))
    await db.flush()
    return True


async def _get_or_create_promotion(db, data: dict) -> bool:
    existing = (await db.execute(
        select(Promotion).where(Promotion.title == data["title"])
    )).scalar_one_or_none()
    if existing:
        return False
    db.add(Promotion(**data))
    await db.flush()
    return True


async def run_seed(db) -> dict[str, int]:
    """写入种子数据，返回各类新增条数。已存在的一律跳过。"""
    written = {"categories": 0, "products": 0, "cases": 0, "promotions": 0}

    # 分类：一级 + 子分类，商品挂在子分类下
    leaf_ids: dict[str, object] = {}
    for idx, (top_name, sort_order, children) in enumerate(CATEGORIES, start=1):
        top, created = await _get_or_create_category(db, top_name, None, sort_order * 10)
        written["categories"] += int(created)

        for c_idx, child_name in enumerate(children, start=1):
            child, child_created = await _get_or_create_category(
                db, child_name, top.id, c_idx
            )
            written["categories"] += int(child_created)
            leaf_ids[child_name] = child.id

    # 商品
    for cat_name, name, age_range, min_qty, base_price, stock, description in PRODUCTS:
        created = await _get_or_create_product(db, {
            "category_id": leaf_ids.get(cat_name),
            "name": name,
            "images": [],
            "description": description,
            "specs": {"适龄": age_range, "起批量": f"{min_qty} 件"},
            "age_range": age_range,
            "safety_certifications": [{"name": "3C认证", "icon": ""}],
            "is_virtual": False,
            "sales_count": 0,
            "stock": stock,
            "min_order_qty": min_qty,
            "pricing_rules": _tiers(base_price, min_qty),
            "status": ProductStatus.ON_SALE,
        })
        written["products"] += int(created)

    # 案例（images 留空：暂无真实案例图，前端用品牌色几何底纹兜底）
    for title, description, category_tags, style_tags, area, sort_order, featured in CASES:
        created = await _get_or_create_case(db, {
            "title": title,
            "description": description,
            "images": [],
            "category_tags": category_tags,
            "style_tags": style_tags,
            "store_area_range": area,
            "sort_order": sort_order,
            "is_featured": featured,
            "status": "published",
        })
        written["cases"] += int(created)

    # 促销：有效期落在「现在」前后，保证 /promotions/active 取得到
    now = datetime.now(timezone.utc)
    window = {"start_time": now - timedelta(days=7), "end_time": now + timedelta(days=180)}
    for title, ptype, rules in PROMOTIONS:
        created = await _get_or_create_promotion(db, {
            "title": title,
            "type": ptype,
            "rules": rules,
            "product_ids": None,
            "is_active": True,
            **window,
        })
        written["promotions"] += int(created)

    return written


async def main() -> None:
    async with async_session_factory() as db:
        written = await run_seed(db)
        await db.commit()
    print("种子数据完成，新增：", written)
    total = sum(written.values())
    if total == 0:
        print("（全部已存在，本次没有新增 —— 幂等生效）")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
```

- [ ] **Step 5: 跑测试，确认通过**

```bash
cd backend && venv/Scripts/python -m pytest tests/test_seed.py -v
```

预期：5 个用例全 **PASS**。

若 `test_seeded_promotions_are_currently_active` 失败并报 naive/aware datetime 比较错误，那是 SQLite 取回的 `DateTime(timezone=True)` 丢了 tzinfo——把断言改成 `p.start_time.replace(tzinfo=None) <= now.replace(tzinfo=None) <= p.end_time.replace(tzinfo=None)`，**不要**改种子数据的方向。

- [ ] **Step 6: 跑全量后端测试**

```bash
cd backend && venv/Scripts/python -m pytest -q
```

预期：**167 passed**（基线 159 + Task 1 的 3 个 + 本任务的 5 个）。

- [ ] **Step 7: 在真实 PostgreSQL 上跑两遍 —— 本机推迟，留到服务器执行**

> **用户已裁决：本机不做这一步**（同 Task 1 Step 6）。**执行者不要启动 Docker、不要建容器、不要卡在这里。**
> 提交即可，并在报告里写明「种子在真实 PG 上的幂等性与 5 个 tab 接口的数据验证未在本机执行，已推迟到服务器」。
>
> 好消息是这一步的本地替代是最强的一处：`test_seed_is_idempotent_from_partial_state` 走的 SQLite 是真库（不是
> mock），「分类已建、商品未建」的半有半无状态在 SQLite 上就能真实复现。**本机唯一验不到的**是
> `JSON` 列与 `DateTime(timezone=True)` 在 PG 上的行为差异——种子本身不写 JSON 查询，所以风险比 Task 1 小得多。

```bash
cd backend
export DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:55432/hxmall'   # Task 1 起的容器
python -m scripts.seed
python -m scripts.seed
```

预期：第一遍输出新增条数；第二遍输出 `新增：{'categories': 0, 'products': 0, 'cases': 0, 'promotions': 0}` 并打印「幂等生效」。

然后确认 5 个 tab 页依赖的接口都有数据：

```bash
BASE='http://localhost:8000/api/v1'
curl -s "$BASE/products?page=1&page_size=5"  | jq '.data.total'   # 预期 > 0
curl -s "$BASE/categories"                   | jq 'length'         # 预期 > 0
curl -s "$BASE/cases?page=1&page_size=5"     | jq '.data.total'   # 预期 > 0
curl -s "$BASE/cases/featured"               | jq '.data | length' # 预期 > 0（首页设计案例区）
curl -s "$BASE/promotions/active" | jq '.data | length'            # 预期 > 0 且不是 500
```

最后一条是这次 B1+B3 的合拢点：**在 B1 之前它返回 500，在 B1 之后返回 `[]`，在 B3 之后才有内容。**

- [ ] **Step 8: 提交**

```bash
cd backend
git add scripts/__init__.py scripts/seed.py tests/test_seed.py
git commit -m "$(cat <<'EOF'
feat(backend): 新增幂等种子脚本

线上商品 total=0、分类=[]、案例 total=0，5 个 tab 页没有内容可显示。
全库唯一的建数据脚本是 deploy/create_admin.py，它只建一个管理员。

幂等策略用「存在即跳过」而非「先删后插」——后者会抹掉运维手工
改过的数据。幂等键是业务唯一键：分类 (name, parent_id)、商品 name、
案例 title、促销 title。

测试重点覆盖「半有半无」的中间状态（分类已建、商品未建），
空库连跑两遍太容易过关。

促销有效期落在当前时间前后，保证 /promotions/active 取得到。

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

## 验收

### A. 本机能验的（全部任务做完后逐条核对）

- [ ] `cd backend && venv/Scripts/python -m pytest -q` → **169 passed**
      （167 是五个任务做完时的数字；全分支最终评审的放行条件又追加了两条用例——
      `test_list_cases_envelope_fields` 与 `test_list_cases_style_filter_matches_multi_tag_arrays`，
      见下方的「验收 D」。控制器在 HEAD `8915af7` 实测：169 passed in 35.60s。）
- [ ] `cd miniapp && npm test` 全绿 → vitest **62 passed (7 files)**，且随后 `vue-tsc --noEmit` 无输出。
      注意 `npm test` 现在**已经包含类型检查**（脚本是 `vitest run && npm run typecheck`），
      所以这一条不再需要单独跑 `npx vue-tsc --noEmit`——单独跑仍然可以，但不是另一道关。
- [ ] `miniapp` 里搜不到 `likeCase`、`/auth/logout`、`params.style_tag`、`style_tag?:`、`tags/styles`、`tags/categories`
      —— **但有三处命中是正确的**，它们是本计划自己加的反向守卫，字符串必须留在那里：
      `cases.test.ts` 的 `not.toHaveProperty('likeCase')`、`cases.test.ts` 那条 `@ts-expect-error` 的
      `{ style_tag: 'ins风' }`、以及 `auth.test.ts` 用例标题里的 `/auth/logout`。
      控制器在 HEAD `41f5bc7` 实测：`likeCase` 2 处、`/auth/logout` 1 处、`style_tag?:` 1 处，**全部落在 `__tests__` 里**；
      `params.style_tag`、`tags/styles`、`tags/categories` 各 0 处。所以判据是「除反向守卫外零命中」，不是「零命中」。
      （**也不能直接搜 `style_tag`**——后端真实字段名是 `style_tags`，含有这个子串，直接搜会假失败。本条就是踩过这个坑之后改的。）
- [ ] `miniapp/src/pages/cases/detail.vue` 里搜不到 `goToProduct` / `formatPrice` / `showError`
      （`noUnusedLocals` 没开，`vue-tsc` 不报这类残骸，只能靠 grep。控制器实测：三者各 0 处，
      `showSuccess` 2 处——import 与 `handleContact` 里的调用，应当保留。）
- [ ] `tests/test_migration_coverage.py` 的三个用例在「临时删掉一列」时会真的失败（Task 1 Step 4b 已证明）

### B. 已推迟到服务器（**用户裁决：本机不做**）

这六条**本机没有执行**，Docker 守护进程未运行且用户选择不在本机启动。它们必须在部署到服务器时补做，
在补做之前，本计划交付的东西**不算在真实 PostgreSQL 上验证过**：

- [ ] 干净 PostgreSQL 上 `alembic upgrade head` 成功，三张表 + 两个枚举类型存在（Task 1 Step 6 检查点 A）
- [ ] `alembic downgrade -1 && alembic upgrade head` 成功（检查点 B）
- [ ] 表已存在的库上 `upgrade head` 不抛 `DuplicateTable`（检查点 C）
- [ ] 枚举类型残留、表不存在的库上 `upgrade head` 的表现（检查点 D —— **预期会失败**，属已知且已接受；
      处置是手工 `DROP TYPE` 后重跑，不是改代码）
- [ ] `python -m scripts.seed` 连跑两遍，第二遍全 0 新增；`GET /promotions/active` 返回 200 且非空
- [ ] `GET /cases/tags` 返回三个键
- [ ] 真实 PostgreSQL 上 `?style=` / `?category_tag=` 的筛选行为。
      **这一条的等级已被下调，别再照旧读它**：原以为它是「SQLite 与 PG 的 JSON 行为差异，只能上服务器验」，
      但全分支最终评审实测证明那是**误判**——通用 `JSON` 列上的 `.contains([x])` 编译成子串 LIKE，
      只对「恰好是单元素数组」的记录成立，`?style=ins风` 在**本地 SQLite 上就返回 0 条**（种子里有 3 条 ins风 案例）。
      这不是待验的库差异，是当时的确定性缺陷。修法（见「验收 D」）改成应用层过滤，
      不再依赖任何库的 JSON 语义或 LIKE 转义规则，所以本地 SQLite 上的
      `test_list_cases_style_filter_matches_multi_tag_arrays` 即代表线上 PG 行为。
      本项现在只剩「PG 上确实无差异」的确认价值，**不再是「筛选是否可用」的证据**。

最后两条合起来看：`/promotions/active` **在 B1 之前返回 500，B1 之后返回 `[]`，B3 之后才有内容**。

### C. 计划范围之外、已知仍坏的（交付时要单独报告，不要当成回归）

- [ ] `pages/cases/index.vue` 的搜索框**搜了等于没搜**——后端 `list_cases` 没有 `keyword` 参数
      （`app/api/cases.py:34-40`），发出去的 `params.keyword` 被 FastAPI 静默忽略。修它要改后端，不在本次范围。

---

### D. 全分支最终评审的放行条件（第五任务之后追加，不在原计划里）

五个任务各自评审通过后，**全分支组装起来**的最终评审判定「不通过」：三处修复各自正确，
拼在一起时 B2 的用户可见结果（案例 tab 能列、能筛）在真实契约下不成立。以下 5 条是放行条件，现均已修复。

| # | 缺陷 | 处置 | 提交 |
|---|---|---|---|
| C1 | 前端读 `res.data.list`，后端信封字段是 `items` —— 案例 tab 每次抛 `TypeError` 落到错误态，一条都渲染不出；`home/index.vue` 静默为空 | `CaseListResult` 改为 `Paginated<DesignCase>` 别名，两个消费方改读 `items`；后端加信封键集守卫 | `81a83a4` |
| C2 | 标签筛选退化成子串 LIKE，只对单元素数组成立；`?style=ins风` 返回 0 条（库里有 3 条）——分支把「静默无效」变成了「筛了但恒空」 | `list_cases` 改应用层过滤（`style in (c.style_tags or [])`），加多标签用例（先 RED 后 GREEN） | `8ca2c24` |
| I1 | `@ts-expect-error` 接口守卫只在有人手动跑 `vue-tsc` 时才生效，无 CI、无钩子——这才是 C1/C2 能穿过全部逐任务评审的结构性原因 | 加 `typecheck` 脚本，`test` 改为 `vitest run && npm run typecheck` | `e2a9936` |
| M1 | 两处测试 mock 键名写成 `del`，而 `request.ts:208` 导出的是 `delete` | 两处同改（只改一处会让两份 mock 分叉） | `f3ecc90` |
| M4 | 案例详情错误态的「重试」是死按钮：`retry()` 前置 `if (caseData.value?.id)`，而加载失败时 `caseData` 为 `null` | 用 `onLoad` 存下的 `caseId` 作前置与入参 | `8915af7` |

生效后 `design_cases` 的标签筛选不再依赖任何库的 JSON 语义，**本地 SQLite 测试即代表线上 PG 行为**——
这正是此前最根本的失败模式（前端全 mock `../request`、后端全 `create_all`，两个结构性盲区）在筛选这条线上的堵口。

代价，交付时要讲清楚：带标签筛选时把 status+area 过滤后的行整表取回内存再筛。
`design_cases` 是策展型图集（种子 8 条，量级几十），且同一文件的 `list_tags` 本来就是这个写法，
所以量级站得住；不带标签筛选时仍走原 SQL 分页路径。**若这张表将来会长到几万条，这条要重新裁。**

仍无自动化保障的（**交付时如实声明，不得暗示已验证**）：

- C1/C2 的端到端结果（「案例 tab 能列能筛」）——无组件测试、无 E2E 基建，靠两端契约钉住**推出**，不是渲染验证
- M4 全靠读代码确认，没有任何用例执行到新逻辑
- M1 无行为级验证：两份测试都不调 DELETE，改键名后只证明了「mock 键名 == `request.ts:208` 真实导出名」
- 新增的信封锁只钉住**信封字段名**，锁不住「后端返回的 `items` 元素形状，前端是否读得对」
