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
