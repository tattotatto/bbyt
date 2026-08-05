# Phase 4：运营优化 — 实现计划

> **Goal:** 采购分析报表(AI生成)、促销活动引擎、案例UGC、A/B测试框架、性能优化

**Baseline:** 99 tests pass

## Task Groups

### P4-1：AI 采购分析报表
- Create: `backend/app/services/reports.py` — 生成零售商采购分析报告
- Create: `backend/app/api/reports.py` — 报表 API
- AI 调用LLM对零售商的采购数据进行总结分析
- Tests: `tests/test_reports.py`

### P4-2：促销活动引擎
- Create: `backend/app/models/promotion.py` — 促销模型(满减/折扣/限时)
- Create: `backend/app/api/promotions.py` — 促销CRUD + 价格计算
- Create: `backend/app/services/promotion.py` — 促销价格计算
- 小程序商品卡片展示促销标签
- Tests: `tests/test_promotions.py`

### P4-3：案例图库 UGC
- Modify: `backend/app/api/cases.py` — 新增设计师上传端点
- 设计师可提交案例 → 管理员审核后发布
- Tests: 补充案例UGC测试

### P4-4：A/B 测试框架
- Create: `backend/app/services/ab_test.py` — 分流+统计
- 支持 AI 模型 A/B (DeepSeek vs 千问)
- Tests: `tests/test_ab_test.py`

### P4-5：性能优化
- Redis 缓存热门商品/案例
- 数据库查询优化(添加缺失索引)
- 图片懒加载确认
- 压测准备

### P4-6：技术债清偿
- ConversationManager → Redis 存储
- WebSocket 心跳检测
- 账期账单自动生成(Cron)
