/// <reference types="@dcloudio/types" />
declare module '*.vue' {
  import { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module 'uview-plus'

declare let uni: any

// ── 测试用的 node 内置模块 ──────────────────────────────────────────
// tsconfig.json 的 "types" 是白名单，只放行 @dcloudio/types；@types/node 没有
// 安装，本项目也不新增依赖（见计划的 Global Constraints）。但源码扫描型测试
// （src/utils/__tests__/icon-map.test.ts）需要 node:fs / node:path 和 __dirname。
// 这里就近声明用到的那几个 API —— 只有类型，运行时由 vitest 的 node 环境提供。
declare module 'node:fs' {
  export function readFileSync(path: string, encoding: string): string
  export function readdirSync(path: string): string[]
  export function statSync(path: string): { isDirectory(): boolean }
}

declare module 'node:path' {
  export function join(...parts: string[]): string
}

declare const __dirname: string

// ── import.meta.env ────────────────────────────────────────────────
// 同样是因为 "types" 白名单：它挡掉了 vite/client，于是 import.meta.env
// 在整个项目里没有类型（TS2339: Property 'env' does not exist on type
// 'ImportMeta'）。这里按上面 node:* 的同一套做法就近补上 —— 不引
// vite/client，那会把 vite 整套资源模块声明一起拖进来（*.png / *.svg …），
// 和 uni-app 自己的资源处理容易打架，而本项目只用得到开关这一类字符串。
interface ImportMetaEnv {
  /** 见 src/mock/fallback.ts：只有严格的 'true' 才开启演示数据兜底 */
  readonly VITE_DEMO_FALLBACK?: string
  readonly [key: string]: string | boolean | undefined
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
