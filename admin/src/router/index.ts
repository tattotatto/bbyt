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
  // 由后端托管在 /admin 路径，history 模式需带 /admin/ 前缀
  history: createWebHistory('/admin/'),
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
