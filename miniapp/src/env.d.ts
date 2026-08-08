/// <reference types="@dcloudio/types" />
declare module '*.vue' {
  import { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module 'uview-plus'

declare let uni: any
