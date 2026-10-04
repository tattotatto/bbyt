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


def _column_from_call(call: ast.Call) -> tuple[str, bool] | None:
    """从 sa.Column('name', ..., nullable=False) 里取出 (列名, 是否非空)。

    迁移里没写 nullable= 时按 SQLAlchemy 的真实默认值 nullable=True 处理。
    这是事实而非猜测：sa.Column 省略 nullable 时列确实可空，如果这里返回
    「不比较」，那么 sa.Column('x', sa.Boolean()) 配 Mapped[bool] 的漂移
    就会被静默放过。
    """
    if not isinstance(call.func, ast.Attribute) or call.func.attr != "Column" or not call.args:
        return None
    name = _str_literal(call.args[0])
    if not name:
        return None
    nullable = True
    for kw in call.keywords:
        if kw.arg == "nullable" and isinstance(kw.value, ast.Constant):
            nullable = bool(kw.value.value)
    return name, nullable


def _columns_created_by_migrations() -> dict[str, dict[str, bool]]:
    """{表名: {列名: 是否非空}}，合并 create_table 与后续的 add_column。"""
    out: dict[str, dict[str, bool]] = {}
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
    """迁移建出来的列，必须和模型逐列对得上（列名 + 可空性）。

    可空性按 sa.Column 的真实语义比较：迁移里省略 nullable= 等同于
    nullable=True，而不是「不比较」。
    """
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
            if col not in model_cols:
                continue
            actual = model_table.columns[col].nullable
            if actual != nullable:
                problems.append(
                    f"{table}.{col}: 迁移写 nullable={nullable}，模型是 nullable={actual}"
                )

    assert problems == [], (
        "迁移与模型的列定义对不上：\n  " + "\n  ".join(problems)
    )
