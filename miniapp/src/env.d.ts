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
