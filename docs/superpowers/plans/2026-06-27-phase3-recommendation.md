# Phase 3：智能推荐 + 知识库深化 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-group by task-group. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** "小暖"记住用户购买习惯、主动精准推荐；知识库支持文档上传解析和对话学习；千问模型接入推荐场景；账期授信管理上线。

**Architecture:** 用户画像作为离线计算模块（订单完成后异步更新），推荐引擎基于画像+规则+季节性策略。知识库增加文档解析管道和对话沉淀机制。千问模型与 DeepSeek 并列接入模型路由层。账期管理作为独立的业务模块。

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, Redis Pub/Sub, python-docx, PyPDF2, openpyxl, qwen-api (OpenAI-compatible)

**Design Doc:** `docs/superpowers/specs/2026-06-26-b2b-mall-design.md` (Sections 十-十二)

**Phase 2 Baseline:** 73 tests pass. AI 对话下单闭环完成。知识库基础版（商品同步+手动录入）。

---

## Global Constraints

- 不破坏现有 73 tests
- 用户画像计算为异步任务，不阻塞订单完成
- 千问模型 API 与 DeepSeek 使用相同的 OpenAI 兼容接口
- 文档解析限制：PDF < 10MB, Word < 5MB, Excel < 5MB
- 账期管理涉及金额始终以"分"为单位存储
- 所有新 API 延续 `/api/v1/` 前缀 + `APIResponse` 响应封装
- 代码中文注释

---

## Task Group P3-1：用户画像引擎

> **负责人：程序师** | 依赖：Phase 2 | 产出：7维画像计算 + 画像服务

### 文件：
- Create: `backend/app/services/profile.py` — 画像计算引擎
- Create: `backend/app/api/recommendations.py` — 推荐 API
- Create: `backend/tests/test_profile.py` — 画像测试

### 实现要点：
1. **画像计算函数** `compute_user_profile(user_id, db)` — 读取历史订单，计算品类偏好/适龄段偏好/价格带/品牌/采购周期/采购量/季节性偏好
2. **画像存储** — 序列化到 `retailer_profiles.purchase_history_summary` JSON 字段
3. **季节性识别** — 品类×月份交叉分析（游泳=6-8月, 护肤=9-11月, 健康=全年）
4. **画像更新时机** — 订单完成后通过 Redis Pub/Sub 触发异步计算

### 验收：
- `compute_user_profile` 空订单历史 → 返回默认画像
- `compute_user_profile` 有订单历史 → 品类偏好正确加权
- 季节性偏好识别正确（游泳设备夏季权重高）
- `pytest tests/test_profile.py -v` 通过

---

## Task Group P3-2：推荐引擎

> **负责人：程序师** | 依赖：P3-1 | 产出：5种推荐场景

### 文件：
- Create: `backend/app/services/recommender.py` — 推荐引擎
- Modify: `backend/app/ai/ws_handler.py` — AI 对话推荐集成画像
- Create: `backend/tests/test_recommender.py`

### 实现要点：
1. **首页推荐** `get_homepage_recommendations(user_id, db)` — 基于品类偏好+季节性，返回 Top-10 商品
2. **对话推荐增强** — ws_handler 中在 RECOMMEND 意图时，注入用户画像到商品搜索排序
3. **补货提醒** `get_restock_suggestions(user_id, db)` — 根据采购周期预测下次补货时间
4. **新品匹配** `match_new_products(user_id, db)` — 新品匹配零售商偏好
5. **季节换品提醒** 返回即将到来的季节对应品类

### 验收：
- 首页推荐按用户偏好排序
- 对话推荐商品优先显示符合画像的
- 补货建议基于采购周期

---

## Task Group P3-3：知识库深化

> **负责人：程序师** | 依赖：P2-4 | 产出：文档解析 + 对话学习 + 季节权重

### 文件：
- Create: `backend/app/ai/knowledge/parser.py` — PDF/Word/Excel 解析
- Modify: `backend/app/ai/knowledge/engine.py` — 增加季节性权重调整
- Modify: `backend/app/api/knowledge.py` — 增加文档上传端点
- Modify: `backend/app/ai/ws_handler.py` — 对话成功下单后提取学习
- Create: `backend/tests/test_knowledge_parser.py`

### 实现要点：
1. **文档解析** `parse_document(file_path, file_type)` — PDF(PyPDF2), Word(python-docx), Excel(openpyxl)
2. **上传端点** `POST /api/v1/knowledge/upload` — 上传文档→解析→分段→Embedding→存储
3. **对话学习** — 对话成功下单时，标记对话链为有效→提取关键推荐话术→运营审核后入库
4. **季节权重** — 根据当前月份动态调整知识条目权重

### 验收：
- 上传 PDF → 解析成功 → 知识条目创建
- 上传 Word → 解析成功
- 对话学习标记正确

---

## Task Group P3-4：千问模型接入

> **负责人：程序师** | 依赖：P2-1 | 产出：千问与 DeepSeek 并列可用

### 文件：
- Modify: `backend/app/config.py` — 添加千问配置
- Modify: `backend/app/ai/llm_client.py` — 添加千问支持
- Modify: `backend/app/ai/model_router.py` — 模型路由（推荐场景→千问）

### 实现要点：
1. 千问 API 兼容 OpenAI 格式 → `AsyncOpenAI(base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")`
2. 路由策略：推荐→千问，下单→DeepSeek，RAG→DeepSeek
3. 容灾：任意模型故障 → 自动切另一模型

### 验收：
- 千问客户端创建成功
- 路由策略根据场景正确选择模型
- 降级切换正常

---

## Task Group P3-5：账期授信管理

> **负责人：程序师** | 依赖：Phase 1 订单系统 | 产出：账期额度+账单+还款

### 文件：
- Create: `backend/app/services/credit.py` — 账期服务
- Create: `backend/app/api/credit.py` — 账期 API
- Create: `backend/app/models/bill.py` — 账单模型
- Create: `backend/app/schemas/credit.py`
- Create: `backend/tests/test_credit.py`

### 实现要点：
1. **额度检查** — 下单时 `credit_balance + 本次金额 ≤ credit_limit`
2. **额度冻结** — 下单时冻结相应额度，订单完成后转为已用
3. **账单生成** — 每月1日自动生成上月账单
4. **还款** — 零售商还款→恢复额度→记录还款流水
5. **逾期处理** — 逾期自动冻结账期权限
6. **API**:
   - `GET /api/v1/credit/balance` — 当前额度
   - `GET /api/v1/credit/bills` — 账单列表
   - `POST /api/v1/credit/repay` — 还款

### 验收：
- 额度内正常下单
- 超额拒绝
- 还款恢复额度

---

## Task Group P3-6：管理员AI效果看板

> **负责人：程序师+UI设计师** | 依赖：P3-1~P3-3 | 产出：AI 对话效果统计看板

### 文件：
- Create: `backend/app/api/dashboard.py` — 看板 API
- Modify: `admin/` — 管理后台新增看板页面

### 实现要点：
1. **统计指标** — 对话总数/下单转化率/推荐点击率/知识库命中率/模型调用量
2. **趋势图** — 按日/周的对话量和转化率趋势
3. **模型对比** — DeepSeek vs 千问的效果对比

---

## 执行顺序

```
P3-1 (用户画像) ──┬── P3-2 (推荐引擎) ──────────────────────┐
                  │                                          │
P3-3 (知识库深化) ─┼── P3-4 (千问接入) ── P3-6 (AI看板) ────┤
                  │                                          │
P3-5 (账期管理) ──┴──────────────────────────────────────────┘
```

P3-1, P3-3, P3-4, P3-5 可并行派发。P3-2 依赖 P3-1。P3-6 依赖 P3-1~P3-3。

---

## 自检

| 检查项 | 状态 |
|--------|------|
| Spec 十一（用户画像+推荐）→ P3-1, P3-2 | ✅ |
| Spec 十（知识库深化）→ P3-3 | ✅ |
| Spec 十二（千问接入）→ P3-4 | ✅ |
| Spec 八（账期管理）→ P3-5 | ✅ |
| 无 TBD/TODO | ✅ |
| Phase 1/2 兼容 | ✅ |
