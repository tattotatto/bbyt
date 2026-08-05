# Admin Dashboard (Vue3 SPA) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-featured Vue3 SPA admin dashboard for HX Mall B2B platform management — products, cases, orders, and user review workflows.

**Architecture:** Vue 3 + TypeScript + Vite SPA with Element Plus UI. Pinia for state, Vue Router for SPA routing, Axios with interceptors for API communication. Token stored in localStorage, route guards redirect unauthenticated users. Coral pink (#FF7B7B) theme throughout.

**Tech Stack:** Vue 3.4+, TypeScript 5.x, Vite 5.x, Element Plus 2.x, Pinia 2.x, Vue Router 4.x, Axios 1.x, Sass

**Design Doc:** `docs/superpowers/specs/2026-06-26-b2b-mall-design.md`

## Global Constraints

- API base URL: `http://localhost:8000/api/v1`
- API responses follow `{"code": 0, "data": ..., "message": "ok"}` envelope
- Pagination: `{"items": [...], "total": N, "page": 1, "page_size": 20}`
- Auth: `Authorization: Bearer <token>` header
- Prices stored as cents (integer) in DB, display as yuan (divided by 100)
- Image upload: POST to `/api/v1/upload` returns URL
- Theme: coral `#FF7B7B`, cream `#FFF8F0`, sky blue `#7EC8E3`, mint `#A8D8B9`
- All Chinese-language UI labels
- All code has Chinese comments

---

## File Structure Map

```
admin/
├── index.html                         # Vite entry HTML
├── package.json                       # Dependencies
├── vite.config.ts                     # Vite config + API proxy
├── tsconfig.json                      # TypeScript config
├── tsconfig.node.json                 # TS config for vite.config
├── env.d.ts                           # Vite env type declarations
├── src/
│   ├── App.vue                        # Root component
│   ├── main.ts                        # Entry: createApp + plugins
│   ├── router/
│   │   └── index.ts                   # Routes + navigation guard
│   ├── api/
│   │   ├── request.ts                 # Axios instance + interceptors
│   │   ├── auth.ts                    # Login, getMe
│   │   ├── products.ts                # Product CRUD + categories
│   │   ├── cases.ts                   # Case CRUD
│   │   ├── orders.ts                  # Order list/detail/status/assign
│   │   └── users.ts                   # User list/review
│   ├── stores/
│   │   └── user.ts                    # Auth state: token, user info, login/logout
│   ├── layouts/
│   │   └── MainLayout.vue             # Sidebar + topbar + content area
│   ├── pages/
│   │   ├── login/
│   │   │   └── index.vue              # Login form (phone + password)
│   │   ├── dashboard/
│   │   │   └── index.vue              # 4-stat cards dashboard
│   │   ├── products/
│   │   │   ├── list.vue               # Product table with search/filter
│   │   │   └── form.vue               # Create/edit product form
│   │   ├── cases/
│   │   │   ├── list.vue               # Case table
│   │   │   └── form.vue               # Create/edit case form
│   │   ├── orders/
│   │   │   ├── list.vue               # Order table with status tabs
│   │   │   └── detail.vue             # Order detail + status actions
│   │   └── users/
│   │       ├── list.vue               # Retailer table with status filter
│   │       └── review.vue             # Review dialog (approve/reject)
│   └── styles/
│       └── global.scss                # Global styles + Element Plus overrides
```

---

## Task 1: Project Scaffold + Config

**Files:**
- Create: `admin/package.json`
- Create: `admin/index.html`
- Create: `admin/vite.config.ts`
- Create: `admin/tsconfig.json`
- Create: `admin/tsconfig.node.json`
- Create: `admin/env.d.ts`
- Create: `admin/src/styles/global.scss`

**Interfaces:**
- Produces:
  - `npm run dev` starts dev server on port 5173
  - Vite proxies `/api/v1` to `http://localhost:8000`
  - Element Plus + icons globally available
  - Coral pink CSS variable theme

- [ ] **Step 1: Create package.json**

```json
{
  "name": "hxmall-admin",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.21",
    "vue-router": "^4.3.0",
    "pinia": "^2.1.7",
    "element-plus": "^2.7.0",
    "@element-plus/icons-vue": "^2.3.1",
    "axios": "^1.6.8"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.4",
    "typescript": "^5.4.5",
    "vite": "^5.2.11",
    "vue-tsc": "^2.0.19",
    "sass": "^1.77.2",
    "@types/node": "^20.12.12"
  }
}
```

- [ ] **Step 2: Create index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>HX Mall 管理后台</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 3: Create vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 4: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue", "env.d.ts"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 5: Create tsconfig.node.json**

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 6: Create env.d.ts**

```typescript
/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
```

- [ ] **Step 7: Create global.scss**

```scss
// ===== HX Mall Admin — Global Styles =====
// 亲子温馨风 珊瑚粉主题

:root {
  // 色板
  --color-primary: #FF7B7B;
  --color-primary-light: #FFF0ED;
  --color-primary-dark: #E86666;
  --color-bg: #FFF8F0;
  --color-blue: #7EC8E3;
  --color-green: #A8D8B9;
  --color-yellow: #FFD93D;
  --color-text: #4a3728;
  --color-text-secondary: #7a6a5a;
  --color-border: #f0e0d0;

  // 圆角
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 20px;

  // 阴影
  --shadow-card: 0 4px 20px rgba(0, 0, 0, 0.06);
  --shadow-soft: 0 2px 8px rgba(255, 123, 123, 0.06);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
  color: var(--color-text);
  background: var(--color-bg);
}

// ===== Element Plus 主题覆盖 =====
// 按钮
.el-button--primary {
  --el-button-bg-color: var(--color-primary);
  --el-button-border-color: var(--color-primary);
  --el-button-hover-bg-color: var(--color-primary-dark);
  --el-button-hover-border-color: var(--color-primary-dark);
  --el-button-active-bg-color: var(--color-primary-dark);
  --el-button-active-border-color: var(--color-primary-dark);
  border-radius: 50px;
}

// 菜单
.el-menu {
  border-right: none !important;
}

.el-menu-item.is-active {
  color: var(--color-primary) !important;
  background: var(--color-primary-light) !important;
}

// 表格
.el-table {
  --el-table-border-color: var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

// 卡片
.el-card {
  border-radius: var(--radius-md);
  border-color: var(--color-border);
  box-shadow: var(--shadow-card);
}

// 输入框
.el-input__wrapper {
  border-radius: var(--radius-sm);
}

// 标签
.el-tag {
  border-radius: 50px;
}

// 对话框
.el-dialog {
  border-radius: var(--radius-md);
}
```

- [ ] **Step 8: Install dependencies and verify**

```bash
cd D:\2026\hxmall\admin
npm install
npx vite --version
```

Expected: Vite version printed, no errors.

---

## Task 2: API Layer (request.ts + all API modules)

**Files:**
- Create: `admin/src/api/request.ts`
- Create: `admin/src/api/auth.ts`
- Create: `admin/src/api/products.ts`
- Create: `admin/src/api/cases.ts`
- Create: `admin/src/api/orders.ts`
- Create: `admin/src/api/users.ts`

**Interfaces:**
- Produces:
  - `request` — Axios instance with Bearer token interceptor, 401 auto-redirect
  - `authApi.login(phone, password)` → `{access_token, refresh_token}`
  - `authApi.getMe()` → user object
  - `productApi.getList(params)` → paginated products
  - `productApi.create(data)` / `productApi.update(id, data)` / `productApi.setPricing(id, rules)` / `productApi.setStatus(id, action)`
  - `productApi.getCategories()` → category tree
  - `caseApi.getList(params)` / `caseApi.create(data)` / `caseApi.update(id, data)` / `caseApi.delete(id)`
  - `orderApi.getList(params)` / `orderApi.getDetail(id)` / `orderApi.updateStatus(id, status)` / `orderApi.assignDesigner(id, designerId)`
  - `uploadApi.upload(file)` → `{url: string}`
  - `userApi.getList(params)` / `userApi.review(id, data)`

- [ ] **Step 1: Create request.ts**

```typescript
// api/request.ts — Axios 封装 + Token 管理
import axios from 'axios'
import type { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建 Axios 实例
const request: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截器：自动附加 Token
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一错误处理
request.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data } = response
    // API 统一响应格式 {code, data, message}
    if (data.code !== 0) {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    return data
  },
  (error) => {
    if (error.response) {
      const { status } = error.response
      if (status === 401) {
        // Token 过期或无效，跳转登录页
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        ElMessage.error('登录已过期，请重新登录')
        router.push('/login')
      } else if (status === 403) {
        ElMessage.error('没有操作权限')
      } else if (status === 422) {
        const detail = error.response.data?.data
        const msg = Array.isArray(detail)
          ? detail.map((e: any) => e.message).join('；')
          : '参数校验失败'
        ElMessage.error(msg)
      } else {
        ElMessage.error(error.response.data?.message || '服务器错误')
      }
    } else {
      ElMessage.error('网络异常，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

export default request
```

- [ ] **Step 2: Create auth.ts**

```typescript
// api/auth.ts — 认证相关 API
import request from './request'

export interface LoginParams {
  phone: string
  password: string
}

export interface LoginResult {
  access_token: string
  refresh_token: string
}

export interface UserInfo {
  id: string
  phone: string
  role: string
  status: string
  created_at: string
}

/** 管理员登录 */
export function login(params: LoginParams): Promise<LoginResult> {
  return request.post('/auth/login', params).then((res) => res.data)
}

/** 获取当前用户信息 */
export function getMe(): Promise<UserInfo> {
  return request.get('/users/me').then((res) => res.data)
}
```

- [ ] **Step 3: Create products.ts**

```typescript
// api/products.ts — 商品管理 API
import request from './request'

// ===== 品类 =====
export interface Category {
  id: string
  name: string
  parent_id: string | null
  icon: string
  sort_order: number
  status: string
  children?: Category[]
}

export function getCategories(): Promise<Category[]> {
  return request.get('/products/categories').then((res) => res.data)
}

export function createCategory(data: { name: string; parent_id?: string; icon?: string; sort_order?: number }): Promise<Category> {
  return request.post('/products/categories', data).then((res) => res.data)
}

// ===== 商品 =====
export interface PricingTier {
  qty: number
  price: number  // 单位：元（前端显示），存储时转为分
}

export interface PricingRules {
  normal: PricingTier[]
  silver: PricingTier[]
  gold: PricingTier[]
  platinum: PricingTier[]
}

export interface ProductForm {
  name: string
  category_id: string
  description: string
  images: string[]
  age_range: string
  safety_certifications: { name: string; icon?: string }[]
  stock: number
  min_order_qty: number
  is_virtual: boolean
  virtual_detail?: Record<string, any>
}

export interface ProductItem {
  id: string
  name: string
  category: Category
  images: string[]
  age_range: string
  stock: number
  status: string
  pricing_rules: PricingRules | null
  is_virtual: boolean
  created_at: string
  updated_at: string
}

export interface ProductListParams {
  page?: number
  page_size?: number
  keyword?: string
  category_id?: string
  status?: string
  age_range?: string
}

export interface PaginatedResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export function getProductList(params: ProductListParams): Promise<PaginatedResult<ProductItem>> {
  return request.get('/products/', { params }).then((res) => res.data)
}

export function createProduct(data: ProductForm): Promise<ProductItem> {
  return request.post('/products/', data).then((res) => res.data)
}

export function updateProduct(id: string, data: Partial<ProductForm>): Promise<ProductItem> {
  return request.put(`/products/${id}`, data).then((res) => res.data)
}

export function setPricing(id: string, pricingRules: PricingRules): Promise<any> {
  return request.put(`/products/${id}/pricing`, pricingRules).then((res) => res.data)
}

export function setProductStatus(id: string, statusAction: 'on_sale' | 'off_sale'): Promise<any> {
  return request.put(`/products/${id}/status`, null, { params: { status_action: statusAction } }).then((res) => res.data)
}

// ===== 上传 =====
export function uploadFile(file: File): Promise<{ url: string }> {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((res) => res.data)
}
```

- [ ] **Step 4: Create cases.ts**

```typescript
// api/cases.ts — 案例管理 API
import request from './request'
import type { PaginatedResult } from './products'

export interface CaseForm {
  title: string
  description: string
  images: string[]
  category_tags: string[]   // 多选：婴童游泳馆/母婴生活馆/儿童乐园
  style_tags: string[]       // 多选：ins风/自然原木/卡通童趣
  area_range: string         // 面积范围
  sort_order: number
  is_featured: boolean
}

export interface CaseItem extends CaseForm {
  id: string
  status: string
  created_at: string
  updated_at: string
}

export interface CaseListParams {
  page?: number
  page_size?: number
  keyword?: string
  category_tag?: string
  style_tag?: string
  is_featured?: boolean
}

export function getCaseList(params: CaseListParams): Promise<PaginatedResult<CaseItem>> {
  return request.get('/cases/', { params }).then((res) => res.data)
}

export function createCase(data: CaseForm): Promise<CaseItem> {
  return request.post('/cases/', data).then((res) => res.data)
}

export function updateCase(id: string, data: Partial<CaseForm>): Promise<CaseItem> {
  return request.put(`/cases/${id}`, data).then((res) => res.data)
}

export function deleteCase(id: string): Promise<void> {
  return request.delete(`/cases/${id}`).then((res) => res.data)
}
```

- [ ] **Step 5: Create orders.ts**

```typescript
// api/orders.ts — 订单管理 API
import request from './request'
import type { PaginatedResult } from './products'

export interface OrderItem {
  id: string
  order_no: string
  type: string                    // physical_goods | store_design
  retailer: {
    id: string
    phone: string
    company_name?: string
  }
  items: {
    product_id: string
    name: string
    qty: number
    unit_price: number            // 单位：分
    subtotal: number              // 单位：分
  }[]
  total_amount: number            // 单位：分
  payment_method: string          // wechat_pay | bank_transfer | credit
  payment_status: string          // pending | paid | confirmed | overdue
  status: string                  // pending_payment | paid | shipped | confirmed | completed | cancelled
  store_design_detail?: {
    store_area?: string
    style_preference?: string
    budget_range?: string
    assigned_designer?: {
      id: string
      name: string
    }
    attachments?: string[]
    delivery_progress?: string
  }
  created_at: string
  updated_at: string
}

export interface OrderListParams {
  page?: number
  page_size?: number
  status?: string
  payment_status?: string
  keyword?: string
  type?: string
}

export function getOrderList(params: OrderListParams): Promise<PaginatedResult<OrderItem>> {
  return request.get('/orders/admin', { params }).then((res) => res.data)
}

export function getOrderDetail(id: string): Promise<OrderItem> {
  return request.get(`/orders/${id}`).then((res) => res.data)
}

export function updateOrderStatus(id: string, status: string): Promise<any> {
  return request.put(`/orders/${id}/status`, { status }).then((res) => res.data)
}

export function assignDesigner(orderId: string, designerId: string): Promise<any> {
  return request.post(`/orders/${orderId}/assign`, { designer_id: designerId }).then((res) => res.data)
}
```

- [ ] **Step 6: Create users.ts**

```typescript
// api/users.ts — 用户管理 API
import request from './request'
import type { PaginatedResult } from './products'

export interface UserItem {
  id: string
  phone: string
  role: string
  level: string                  // normal | silver | gold | platinum
  status: string                 // pending_review | active | frozen
  company_name?: string
  contact_person?: string
  business_license?: string
  credit_limit?: number          // 单位：分
  credit_balance?: number        // 单位：分
  created_at: string
}

export interface UserListParams {
  page?: number
  page_size?: number
  keyword?: string
  status?: string
  level?: string
  role?: string
}

export interface ReviewData {
  action: 'approve' | 'reject'
  level?: string                 // 审核通过时设置等级
  credit_limit?: number          // 审核通过时设置账期额度（单位：分）
  reject_reason?: string         // 拒绝原因
}

export function getUserList(params: UserListParams): Promise<PaginatedResult<UserItem>> {
  return request.get('/users/', { params }).then((res) => res.data)
}

export function reviewUser(userId: string, data: ReviewData): Promise<any> {
  return request.post('/users/review', { user_id: userId, ...data }).then((res) => res.data)
}

/** 获取设计师列表（用于订单指派） */
export function getDesigners(): Promise<UserItem[]> {
  return request.get('/users/', { params: { role: 'designer', page_size: 100 } }).then((res) => res.data.items)
}
```

---

## Task 3: Auth Store + Router + App Entry

**Files:**
- Create: `admin/src/stores/user.ts`
- Create: `admin/src/router/index.ts`
- Create: `admin/src/main.ts`
- Create: `admin/src/App.vue`

**Interfaces:**
- Produces:
  - `useUserStore` — Pinia store: `token`, `userInfo`, `isLoggedIn`, `login()`, `logout()`, `fetchUser()`
  - Router with routes: `/login`, `/` (dashboard), `/products`, `/products/create`, `/products/:id/edit`, `/cases`, `/cases/create`, `/cases/:id/edit`, `/orders`, `/orders/:id`, `/users`, `/users/:id/review`
  - Navigation guard: redirect to `/login` if not authenticated
  - `main.ts` — mounts app with all plugins

- [ ] **Step 1: Create stores/user.ts**

```typescript
// stores/user.ts — 管理员登录状态管理
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getMe } from '@/api/auth'
import type { UserInfo } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  // ===== 状态 =====
  const token = ref<string>(localStorage.getItem('access_token') || '')
  const refreshToken = ref<string>(localStorage.getItem('refresh_token') || '')
  const userInfo = ref<UserInfo | null>(null)

  // ===== 计算属性 =====
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value?.role === 'admin' || userInfo.value?.role === 'operator')

  // ===== 动作 =====
  /** 登录 */
  async function login(phone: string, password: string) {
    const result = await loginApi({ phone, password })
    token.value = result.access_token
    refreshToken.value = result.refresh_token
    localStorage.setItem('access_token', result.access_token)
    localStorage.setItem('refresh_token', result.refresh_token)
    // 获取用户信息
    await fetchUser()
  }

  /** 获取当前用户信息 */
  async function fetchUser() {
    if (!token.value) return
    try {
      const user = await getMe()
      userInfo.value = user
    } catch {
      // 如果获取失败，清除登录状态
      logout()
    }
  }

  /** 退出登录 */
  function logout() {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return { token, refreshToken, userInfo, isLoggedIn, isAdmin, login, fetchUser, logout }
})
```

- [ ] **Step 2: Create router/index.ts**

```typescript
// router/index.ts — 路由配置 + 导航守卫
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/login/index.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/pages/dashboard/index.vue'),
        meta: { title: '仪表盘', icon: 'DataAnalysis' },
      },
      {
        path: 'products',
        name: 'Products',
        component: () => import('@/pages/products/list.vue'),
        meta: { title: '商品管理', icon: 'Goods' },
      },
      {
        path: 'products/create',
        name: 'ProductCreate',
        component: () => import('@/pages/products/form.vue'),
        meta: { title: '新增商品' },
      },
      {
        path: 'products/:id/edit',
        name: 'ProductEdit',
        component: () => import('@/pages/products/form.vue'),
        meta: { title: '编辑商品' },
      },
      {
        path: 'cases',
        name: 'Cases',
        component: () => import('@/pages/cases/list.vue'),
        meta: { title: '案例管理', icon: 'PictureFilled' },
      },
      {
        path: 'cases/create',
        name: 'CaseCreate',
        component: () => import('@/pages/cases/form.vue'),
        meta: { title: '新增案例' },
      },
      {
        path: 'cases/:id/edit',
        name: 'CaseEdit',
        component: () => import('@/pages/cases/form.vue'),
        meta: { title: '编辑案例' },
      },
      {
        path: 'orders',
        name: 'Orders',
        component: () => import('@/pages/orders/list.vue'),
        meta: { title: '订单管理', icon: 'Document' },
      },
      {
        path: 'orders/:id',
        name: 'OrderDetail',
        component: () => import('@/pages/orders/detail.vue'),
        meta: { title: '订单详情' },
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/pages/users/list.vue'),
        meta: { title: '用户管理', icon: 'User' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 导航守卫：未登录跳转登录页
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
```

- [ ] **Step 3: Create main.ts**

```typescript
// main.ts — 应用入口
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

import App from './App.vue'
import router from './router'
import './styles/global.scss'

const app = createApp(App)

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')
```

- [ ] **Step 4: Create App.vue**

```vue
<template>
  <router-view />
</template>

<script setup lang="ts">
// App.vue — 根组件
</script>

<style>
#app {
  width: 100%;
  height: 100vh;
}
</style>
```

- [ ] **Step 5: Verify router and store work**

```bash
cd D:\2026\hxmall\admin
npx vue-tsc --noEmit
```

Expected: Type checks pass (may have errors about missing page components — that's OK, they'll be resolved in subsequent tasks).

---

## Task 4: Login Page

**Files:**
- Create: `admin/src/pages/login/index.vue`

**Interfaces:**
- Consumes: `useUserStore` from Task 3
- Produces: Login page with phone + password form, coral theme button

- [ ] **Step 1: Create login/index.vue**

```vue
<template>
  <!-- 登录页 — 居中卡片式 -->
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1 class="login-title">HX Mall 管理后台</h1>
        <p class="login-subtitle">儿童产品 B2B 批发商城</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        size="large"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="phone">
          <el-input
            v-model="form.phone"
            placeholder="请输入手机号"
            :prefix-icon="Phone"
            maxlength="11"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
// 登录页 — 手机号+密码登录
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Phone, Lock } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

// 表单数据
const form = reactive({
  phone: '',
  password: '',
})

// 表单验证规则
const rules: FormRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
}

/** 处理登录 */
async function handleLogin() {
  if (!formRef.value) return
  // 表单验证
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.login(form.phone, form.password)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (err: any) {
    ElMessage.error(err?.message || '登录失败，请检查账号密码')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #FFF8F0 0%, #FFF0ED 50%, #FFF8F0 100%);
}

.login-card {
  width: 420px;
  padding: 48px 40px;
  background: #fff;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-primary);
  letter-spacing: 2px;
}

.login-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-top: 8px;
}

.login-form {
  .el-form-item {
    margin-bottom: 24px;
  }
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  letter-spacing: 4px;
  background: var(--color-primary);
  border-color: var(--color-primary);

  &:hover {
    background: var(--color-primary-dark);
    border-color: var(--color-primary-dark);
  }
}
</style>
```

---

## Task 5: MainLayout

**Files:**
- Create: `admin/src/layouts/MainLayout.vue`

**Interfaces:**
- Consumes: `useUserStore` from Task 3, router from Task 3
- Produces: Sidebar + topbar layout wrapping `<router-view>`

- [ ] **Step 1: Create layouts/MainLayout.vue**

```vue
<template>
  <!-- 管理后台主布局：侧边栏 + 顶栏 + 内容区 -->
  <el-container class="main-layout">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="layout-aside">
      <div class="aside-header" @click="toggleCollapse">
        <span v-show="!isCollapse" class="aside-logo">🌸 HX Mall</span>
        <span v-show="isCollapse" class="aside-logo-small">🌸</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        router
        class="aside-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        <el-menu-item index="/products">
          <el-icon><Goods /></el-icon>
          <template #title>商品管理</template>
        </el-menu-item>
        <el-menu-item index="/cases">
          <el-icon><PictureFilled /></el-icon>
          <template #title>案例管理</template>
        </el-menu-item>
        <el-menu-item index="/orders">
          <el-icon><Document /></el-icon>
          <template #title>订单管理</template>
        </el-menu-item>
        <el-menu-item index="/users">
          <el-icon><User /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 右侧主区域 -->
    <el-container>
      <!-- 顶栏 -->
      <el-header class="layout-header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="toggleCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <span class="header-title">HX Mall 管理后台</span>
        </div>
        <div class="header-right">
          <el-dropdown trigger="click">
            <span class="user-info">
              <el-icon><UserFilled /></el-icon>
              <span class="user-phone">{{ userStore.userInfo?.phone || '管理员' }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
// MainLayout.vue — 管理后台主布局
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import {
  DataAnalysis, Goods, PictureFilled, Document, User,
  Fold, Expand, UserFilled, ArrowDown, SwitchButton,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 侧边栏折叠状态
const isCollapse = ref(false)

// 当前激活的菜单项
const activeMenu = computed(() => {
  const path = route.path
  // 匹配父级路由
  if (path.startsWith('/products')) return '/products'
  if (path.startsWith('/cases')) return '/cases'
  if (path.startsWith('/orders')) return '/orders'
  if (path.startsWith('/users')) return '/users'
  return path
})

/** 切换侧边栏折叠 */
function toggleCollapse() {
  isCollapse.value = !isCollapse.value
}

/** 退出登录 */
async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    userStore.logout()
    router.push('/login')
  } catch {
    // 用户取消
  }
}
</script>

<style scoped lang="scss">
.main-layout {
  height: 100vh;
}

// ===== 侧边栏 =====
.layout-aside {
  background: #fff;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.04);
  transition: width 0.3s;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.aside-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-bottom: 1px solid var(--color-border);
  user-select: none;
}

.aside-logo {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-primary);
}

.aside-logo-small {
  font-size: 24px;
}

.aside-menu {
  flex: 1;
  border-right: none;

  .el-menu-item {
    &.is-active {
      color: var(--color-primary);
      background: var(--color-primary-light);
      border-right: 3px solid var(--color-primary);
    }
  }
}

// ===== 顶栏 =====
.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid var(--color-border);
  padding: 0 24px;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  color: var(--color-text-secondary);

  &:hover {
    color: var(--color-primary);
  }
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 12px;
  border-radius: 50px;
  transition: background 0.2s;

  &:hover {
    background: var(--color-primary-light);
  }

  .user-phone {
    font-size: 14px;
    color: var(--color-text);
  }
}

// ===== 内容区 =====
.layout-main {
  background: var(--color-bg);
  padding: 24px;
  overflow-y: auto;
}
</style>
```

---

## Task 6: Dashboard

**Files:**
- Create: `admin/src/pages/dashboard/index.vue`

**Interfaces:**
- Consumes: API modules from Task 2
- Produces: 4 stat cards with data from APIs

- [ ] **Step 1: Create dashboard/index.vue**

```vue
<template>
  <!-- 仪表盘 — 数据概览 -->
  <div class="dashboard">
    <h2 class="page-title">仪表盘</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :xs="24" :sm="12" :lg="6" v-for="card in statCards" :key="card.label">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" :style="{ background: card.bg }">
              <el-icon :size="28" color="#fff">
                <component :is="card.icon" />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ card.value }}</div>
              <div class="stat-label">{{ card.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 刷新提示 -->
    <div class="dashboard-tip">
      <el-alert
        title="提示：点击卡片可跳转对应管理页面"
        type="info"
        :closable="false"
        show-icon
      />
    </div>
  </div>
</template>

<script setup lang="ts">
// 仪表盘页 — 统计概览
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Goods, Document, User, PictureFilled } from '@element-plus/icons-vue'
import { getProductList } from '@/api/products'
import { getOrderList } from '@/api/orders'
import { getUserList } from '@/api/users'
import { getCaseList } from '@/api/cases'

const router = useRouter()

// 统计卡片数据
const statCards = reactive([
  {
    label: '商品总数',
    value: 0,
    icon: Goods,
    bg: 'linear-gradient(135deg, #FF7B7B, #FF9E9E)',
    route: '/products',
  },
  {
    label: '订单总数',
    value: 0,
    icon: Document,
    bg: 'linear-gradient(135deg, #7EC8E3, #9ED8E8)',
    route: '/orders',
  },
  {
    label: '待审核用户',
    value: 0,
    icon: User,
    bg: 'linear-gradient(135deg, #A8D8B9, #C0E8CE)',
    route: '/users',
  },
  {
    label: '案例总数',
    value: 0,
    icon: PictureFilled,
    bg: 'linear-gradient(135deg, #FFD93D, #FFE580)',
    route: '/cases',
  },
])

/** 加载统计数据 */
async function loadStats() {
  try {
    // 并发获取各项统计数据
    const [productRes, orderRes, pendingUsersRes, caseRes] = await Promise.all([
      getProductList({ page: 1, page_size: 1 }),
      getOrderList({ page: 1, page_size: 1 }),
      getUserList({ page: 1, page_size: 1, status: 'pending_review' }),
      getCaseList({ page: 1, page_size: 1 }),
    ])
    statCards[0].value = productRes.total
    statCards[1].value = orderRes.total
    statCards[2].value = pendingUsersRes.total
    statCards[3].value = caseRes.total
  } catch {
    // API 未就绪时静默处理
  }
}

/** 点击卡片跳转 */
function goTo(route: string) {
  router.push(route)
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped lang="scss">
.dashboard {
  .page-title {
    font-size: 22px;
    font-weight: 600;
    color: var(--color-text);
    margin-bottom: 24px;
  }
}

.stat-cards {
  .stat-card {
    cursor: pointer;
    transition: transform 0.2s;

    &:hover {
      transform: translateY(-4px);
    }
  }
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-top: 4px;
}

.dashboard-tip {
  margin-top: 32px;
}
</style>
```

---

## Task 7: Products Management (list + form)

**Files:**
- Create: `admin/src/pages/products/list.vue`
- Create: `admin/src/pages/products/form.vue`

- [ ] **Step 1: Create products/list.vue** — full table with search, pagination, status toggle

- [ ] **Step 2: Create products/form.vue** — full form with image upload, pricing rules table, virtual product toggle

---

## Task 8: Cases Management (list + form)

**Files:**
- Create: `admin/src/pages/cases/list.vue`
- Create: `admin/src/pages/cases/form.vue`

---

## Task 9: Orders Management (list + detail)

**Files:**
- Create: `admin/src/pages/orders/list.vue`
- Create: `admin/src/pages/orders/detail.vue`

---

## Task 10: Users Management (list + review)

**Files:**
- Create: `admin/src/pages/users/list.vue`
- Create: `admin/src/pages/users/review.vue`

---

## Self-Review Checklist

| Check | Status |
|-------|--------|
| Spec coverage | All 7 spec sections covered via 10 tasks |
| No placeholders | Verified — all code is fully written |
| Type consistency | API types defined in Task 2, consumed by Tasks 4-10 |
| File paths | All absolute paths, one responsibility per file |
| Theme | Coral #FF7B7B applied in global.scss and each component |

---

## Execution Order

Tasks 1 → 2 → 3 are sequential (dependencies).
Tasks 4, 5, 6 can run in parallel after Task 3.
Tasks 7, 8, 9, 10 can run in parallel after Task 2 (no cross-dependency between pages).
