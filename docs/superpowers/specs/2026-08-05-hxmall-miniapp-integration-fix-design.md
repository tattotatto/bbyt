# HXMall 小程序端联调修复与功能补齐 — 设计文档

日期：2026-08-05
范围：`miniapp/`（uni-app 微信小程序）+ `backend/`（FastAPI）

## 1. 背景与问题

HXMall 是 B2B 儿童产品批发商城（后端 FastAPI + 管理后台 Vue3 + 微信小程序 uni-app）。小程序前端 UI 完成度高（约 80%），但**前后端联调基本未做**，存在以下断点：

1. **登录是 mock**：`stores/user.ts` 生成假 token，后端无微信登录接口。
2. **接口路径不一致**：如小程序调 `/api/v1/categories`，后端实际是 `/api/v1/products/categories`；`getUserProfile` 调 `/user/profile`，后端是 `/users/me`。
3. **字段不一致**：商品（`moq`/`price_tiers`/`specs[]` vs 后端 `min_order_qty`/`pricing_rules`/`specs` dict）、订单（数字状态 vs 字符串枚举、金额"分" vs "元"）、下单参数（`address_id` vs `receiver_*` 平铺）。
4. **后端缺失功能**：`/products/hot`、`/products/new`、`sort` 排序、订单 cancel/confirm/refund、企业资料更新、收藏、购物车、地址簿、浏览记录。
5. **死链页面**：购物车页与"我的"9 个子页面在 `pages.json` 中未注册。
6. **配置不一致**：request/upload/constants 三处 URL 地址互相矛盾（已先行统一到 `baby.mx.yn.cn`）。

## 2. 目标与范围

- 打通小程序端到端主链路：**微信登录 → 浏览 → 商品详情 → 加购 → 下单 → 订单操作**。
- 补齐"我的"中心全部页面与购物车页。
- 后端补齐缺失能力；前端以后端契约为准对齐。
- **不在本次范围**：真实微信支付、优惠券第三方对接（只读占位）、AI 助手深层优化（协议已对齐）。

## 3. 关键决策（已与用户确认）

| 决策点 | 结论 |
|--------|------|
| 前后端对齐基准 | **以后端为准，改前端适配** |
| 前端适配方式 | **B：API 类型直接对齐后端形状，页面逐处改字段**（不引入 adapter 层） |
| 登录方案 | **微信一键登录**；后端自动建号 + `pending_review` 审核；管理员审核通过后可下单 |
| 微信配置 | 可配置 `WECHAT_APPID/SECRET`；无配置或 `dev_` 前缀 code 走**开发模式**签发测试 token |
| 购物车/地址簿/浏览记录 | **全走后端**，力求完整 |
| 优惠券页 | **第三方只读占位**，后续接入第三方平台 |
| 页面补齐 | 购物车页 + "我的"9 个子页全部实现 |
| 执行 | 计划获批后由 Claude 分阶段实现 |

## 4. 总体架构

- **契约基准**：后端现有 FastAPI 路由与 Pydantic schema 是唯一事实来源；前端 `src/api/*.ts` 的类型与调用全部对齐后端。
- **前端状态**：购物车、地址簿、浏览记录、收藏改为后端同步；`user` store 走真实登录；浏览记录含本地兜底。
- **迁移**：通过 alembic 新增 6 项变更（见 §5.4）。
- **审核门禁**：下单接口校验用户 `status == active`。

## 5. 后端改造

### 5.1 认证：微信登录 + 审核门禁

**新增 `POST /api/v1/auth/wx-login`**
- 请求：`{ code: str, user_info?: { nickName?, avatarUrl? } }`
- 逻辑：
  1. 若 `settings.WECHAT_APPID` 为空 或 `code` 以 `dev_` 开头 → **开发模式**：`openid = "dev_" + code`，不调用微信。
  2. 否则调用微信 `jscode2session`（`appid`/`secret`/`js_code`/`grant_type=authorization_code`）换取 `openid`；失败抛 401。
  3. 按 `wx_openid` 查用户；不存在则创建零售商账号：
     - `role=RETAILER`、`level=NORMAL`、`status=PENDING_REVIEW`
     - `wx_openid` 存入；`nickname`/`avatar` 若有则存（`users` 表当前无昵称/头像列——**迁移：`users` 加 `nickname`、`avatar` 列**）。
  4. 生成 `access_token` / `refresh_token`，返回 `{access_token, refresh_token, user_info}`，其中 `user_info` 含 `id/phone/nickname/avatar/role/level/status/company_name/credit_limit/credit_balance`。
- 同步修改：`schemas/user.py` 的 `UserOut` 增加 `nickname`/`avatar` 字段，使 wx-login 返回的用户信息与现有 `/users/me` 一致。
- 复用 `auth_service.create_access_token/create_refresh_token`。

**审核门禁**
- `api/orders.py::place_order` 增加：查询用户，若 `status != ACTIVE` 抛 403「账号审核中，暂不能下单」。
- 管理员（admin/operator）不受此限制（其角色不同，天然通过）。

### 5.2 商品 API

- `GET /products/hot`：on_sale 商品按 `sales_count desc` 排序，limit（默认 10）。
- `GET /products/new`：on_sale 商品按 `created_at desc` 排序，limit（默认 10）。
- `GET /products` 增加 `sort` 参数（默认 `newest`）：`newest`→created_at desc；`sales_desc`→sales_count desc；`price_asc`/`price_desc`→按 pricing_rules 最低阶梯价排序（数据库层无法直接排 JSON，可查询后在内存排序 top-N，或简化为对 `pricing_rules` 的 `normal` 首档价格排序——**实现细节在计划中明确，以内存排序控制分页精度**）。

### 5.3 订单操作

- `POST /orders/{id}/cancel`（用户本人，仅 `status == pending_payment`）→ `cancelled`，追加 timeline。
- `POST /orders/{id}/confirm`（用户本人，`status == shipped`）→ `completed`（确认收货直达完成态，对应前端唯一"已完成"终态）。
- `POST /orders/{id}/refund`（用户本人，`status in (paid, shipped)`）→ `refunding`，追加 timeline。
- 权限：非 admin/operator 时校验 `order.retailer_id == current_user_id`。
- 退款受理：管理员通过 `PUT /orders/{id}/status` 处理（扩展 `OrderStatusUpdate` 的 `status` pattern 为 `^(paid|shipped|confirmed|completed|cancelled|refunding)$`，可将 `refunding → completed|cancelled`）。

### 5.4 个人中心能力

新增模型 + 路由（全部需要鉴权 `get_current_user`）：

| 能力 | 模型（表名） | API |
|------|-------------|-----|
| 企业资料更新 | 复用 `RetailerProfile` | `PUT /users/me/profile`：更新 company_name / business_license / contact_person；仅零售商 |
| 购物车 | `CartItem`（user_id, product_id, spec, quantity, 唯一约束(user_id, product_id, spec)） | `GET /cart`（联表返回商品名/图/单价/库存/MOQ）、`POST /cart`（加购/数量累加）、`PUT /cart/{id}`（改数量）、`DELETE /cart/{id}`（删除）、`DELETE /cart`（清空） |
| 地址簿 | `Address`（user_id, name, phone, province, city, district, detail, is_default） | `GET /user/addresses`、`POST /user/addresses`、`PUT /user/addresses/{id}`、`DELETE /user/addresses/{id}` |
| 浏览记录 | `BrowseHistory`（user_id, product_id, viewed_at；唯一约束(user_id, product_id)，再次浏览更新时间） | `GET /history`（分页倒序）、`POST /history`（记录浏览）、`DELETE /history/{product_id}`、`DELETE /history`（清空） |
| 收藏 | `Favorites`（user_id, product_id, created_at；唯一约束(user_id, product_id)） | `GET /favorites`（分页）、`POST /favorites`（收藏）、`DELETE /favorites/{product_id}`（取消） |

- 路由挂载：`cart` 挂在 `/api/v1/cart`，`history` 挂在 `/api/v1/history`，`addresses` 挂在 `/api/v1/users`（即 `/users/addresses`），`favorites` 挂在 `/api/v1/favorites`。
- 列表类接口统一返回 `PaginatedResponse`。

### 5.5 迁移清单（alembic，共 6 项）

1. `products` 加 `sales_count`（Integer, default 0）
2. `users` 加 `nickname`（String）、`avatar`（String）
3. `cart_items` 表
4. `addresses` 表
5. `browse_history` 表
6. `favorites` 表
7. `OrderStatus` 枚举加 `refunding`（Postgres 原生枚举需 `ALTER TYPE orderstatus ADD VALUE 'refunding'`；SQLite 测试库需重建，见 §7 验证说明）

> 注：第 7 项与前面 6 项并列但类型不同（枚举变更而非新表），计划中单独处理。

### 5.6 后端测试（pytest）

新增/更新 `backend/tests/`：
- `test_wx_login.py`：开发模式（dev_ code）建号/老用户登录、重复登录不重复建号、新用户 `pending_review`
- `test_products.py`：hot / new 排序、sort 参数
- `test_orders.py`：下单门禁（pending_review 403）、cancel/confirm/refund 状态流转与越权 403
- `test_profile.py`：PUT /users/me/profile
- `test_cart.py`：加购/改量/删除/越权
- `test_address.py`：CRUD + 默认地址
- `test_history.py`：记录/列表/清空
- `test_favorites.py`：收藏/取消/列表

## 6. 前端改造（miniapp）

### 6.1 API 层对齐（`src/api/*.ts`）

- `request.ts`：`BASE_URL` 改从 `utils/constants.ts` 的 `API_BASE_URL` 引用（值为 `https://baby.mx.yn.cn/api/v1`）；`upload.ts` 同样引用。
- `auth.ts`：保留/修正 `wxLogin`（真实调用 `/auth/wx-login`）；`getUserProfile` → `/users/me`；删除未用/不符的 `phoneLogin`/`sendVerifyCode` 或保留但标注未用。
- `products.ts`：`getCategories` → `/products/categories`；新增 `getHotProducts`/`getNewProducts` 命中 `/products/hot`、`/products/new`；`Product`/`ProductDetail` 类型改为后端形状（`min_order_qty`、`pricing_rules`、`specs` dict、`age_range`、`safety_certifications` list[dict]、`category` 对象）。
- `orders.ts`：`Order`/`OrderItem` 类型对齐（字符串 `status`、`total_amount` 分、`items` dict 列表、`receiver_*`）；`createOrder` 参数改为后端形状；`cancelOrder`/`confirmReceipt`/`requestRefund` 命中新增端点；地址方法移到新 `address.ts`。
- 新增 `cart.ts`、`address.ts`、`history.ts`、`favorites.ts`。

### 6.2 页面改造

| 页面 | 改动 |
|------|------|
| `home/index` | 分类→`/products/categories`；推荐→`/products/new`；热门→`/products/hot`；角标用后端购物车数量（登录后） |
| `products/index` | 列表类型对齐；sort 传 `sort` 参数；字段改名（moq→min_order_qty 等） |
| `products/detail` | 价格区间/批发价表从 `pricing_rules` 渲染；`unit` 缺省"件"；打开时 `POST /history`；收藏按钮接 `/favorites`；购物车入口→新购物车页 |
| `order/checkout` | 从后端地址簿选地址；`createOrder` 传 `receiver_*` + `payment_method=wechat_pay`；items 从购物车选中项构建 |
| `order/list`、`order/detail` | 字符串状态映射；金额 `/100`；items 后端结构；操作按钮（取消/确认收货/退款）接新端点 |
| `mine/index` | 真实登录流程；子页导航全部生效 |
| 新增 10 页 | `cart`、`mine/company`、`mine/address`、`mine/member`、`mine/favorites`、`mine/history`、`mine/coupons`（只读占位）、`mine/contact`、`mine/settings`、`mine/help` |

### 6.3 Stores

- `user.ts`：`login()` 调真实 `wxLogin`（`uni.login` 拿 code → `/auth/wx-login`）；`userInfo` 用后端返回；删 mock。
- `cart.ts`：改为后端同步——`init`（登录后拉取）、`addItem`/`updateQuantity`/`removeItem` 调 API；未登录时置空。
- 新增 `address.ts`（后端同步）、`history.ts`（后端同步）。
- 新增后端字段映射工具：`src/utils/constants.ts` 的 `ORDER_STATUS` 改为字符串键。

### 6.4 配置

- `utils/constants.ts`：`ORDER_STATUS` 改字符串键；`API_BASE_URL` 保持 `https://baby.mx.yn.cn/api/v1`。
- `pages.json`：注册全部新页面。

## 7. 验证

1. **后端**：`pytest` 全绿（含新增用例）；`alembic upgrade head` 成功。
2. **前端**：`npm run build:mp-weixin` 编译通过；TypeScript 无类型错误。
3. **手动验证清单**（微信开发者工具 + 开发模式登录）：
   - 登录（dev 模式）→ 我的页显示用户信息
   - 首页分类/推荐/热门/轮播加载正常
   - 商品详情价格、批发价表、规格、起订量正确；收藏/取消生效
   - 加购 → 购物车页数量管理 → 结算选地址 → 下单成功
   - 订单列表状态正确；取消（待付款）/确认收货（已发货）/退款流转正确
   - 会员中心、企业资料、浏览记录、优惠券占位页、客服/设置/帮助可访问
4. **SQLite 测试库注意**：`OrderStatus` 枚举加值在 SQLite 下需要 `CREATE TYPE` 不可用——测试库用 SQLite 时按重建表策略处理（alembic `batch_alter_table` 或重置 test.db），Postgres 用 `ALTER TYPE`。

## 8. 执行顺序（4 个 Phase）

- **Phase A 后端补齐**：迁移 → wx-login + 门禁 → 商品 hot/new/sort → 订单三操作 → cart/address/history/favorites/profile → pytest 全绿。
- **Phase B 前端 API 层对齐**：request/constants 接线 → api 层类型/路径 → 登录接入（user store）→ 商品/首页改造。
- **Phase C 下单链路**：结算页 + 地址簿 → 订单列表/详情 → 订单操作按钮。
- **Phase D 页面补齐与收尾**：购物车页 + 我的 9 子页 → 全量构建验证 + 手动清单。

## 9. 不在本次范围（后续）

- 真实微信支付（当前后端 `wechat_pay` 为模拟支付）
- 优惠券第三方平台对接（页面上只读占位）
- 促销/账期的用户侧复杂流转
- AI 助手功能增强
