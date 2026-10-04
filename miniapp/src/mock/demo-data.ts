/**
 * 开发期演示数据。
 *
 * 生产库目前基本是空的（商品 total = 0、分类 = []、案例 total = 0），
 * 设计在「满负荷」下长什么样根本没法验收。这份数据只解决验收问题，
 * 由 VITE_DEMO_FALLBACK 控制，生产构建默认关闭。
 *
 * 字段与真实接口一一对应，类型由 api/ 下的接口约束 —— 对不上会编译报错。
 */
import type { Category } from '../api/types'
import type { ProductListItem } from '../api/products'
import type { DesignCase } from '../api/cases'

export const DEMO_CATEGORIES: Category[] = [
  { id: 'demo-c1', parent_id: null, name: '婴童服饰', icon: null, sort_order: 1, status: 'active', children: [] },
  { id: 'demo-c2', parent_id: null, name: '喂养用品', icon: null, sort_order: 2, status: 'active', children: [] },
  { id: 'demo-c3', parent_id: null, name: '寝居出行', icon: null, sort_order: 3, status: 'active', children: [] },
  { id: 'demo-c4', parent_id: null, name: '洗护用品', icon: null, sort_order: 4, status: 'active', children: [] },
  { id: 'demo-c5', parent_id: null, name: '玩具早教', icon: null, sort_order: 5, status: 'active', children: [] },
]

function product(
  id: string, name: string, age: string, minQty: number,
  priceMin: number, priceMax: number,
): ProductListItem {
  return {
    id, name, images: [], age_range: age, safety_certifications: [{ name: '3C认证' }],
    is_virtual: false, stock: 999, min_order_qty: minQty, status: 'on_sale',
    price_min: priceMin, price_max: priceMax,
  }
}

export const DEMO_PRODUCTS: ProductListItem[] = [
  product('demo-p1', '纯棉长袖连体衣 新生儿爬服', '0-3岁', 10, 33.44, 38),
  product('demo-p2', '宽口径玻璃奶瓶 240ml', '0-3岁', 12, 35.7, 42),
  product('demo-p3', '硅胶辅食碗勺套装', '0-3岁', 24, 13.6, 16),
  product('demo-p4', '实木多功能婴儿床', '0-3岁', 3, 187.2, 260),
  product('demo-p5', '超薄透气纸尿裤 L 码', '0-3岁', 30, 46.4, 58),
  product('demo-p6', '大颗粒益智积木 80 粒', '3-6岁', 20, 41.6, 52),
  product('demo-p7', '轻便折叠婴儿推车', '0-3岁', 4, 288, 380),
  product('demo-p8', '婴儿洗发沐浴二合一 500ml', '0-3岁', 24, 17.6, 22),
]

function designCase(
  id: string, title: string, area: string, styles: string[], categories: string[],
  featured: boolean,
): DesignCase {
  return {
    id, title, description: '', images: [],
    category_tags: categories, style_tags: styles,
    store_area_range: area, is_featured: featured, created_at: null,
  }
}

export const DEMO_CASES: DesignCase[] = [
  designCase('demo-k1', '北欧风儿童房整体方案', '50-100㎡', ['ins风', '自然原木'], ['儿童房'], true),
  designCase('demo-k2', '蒙氏游戏区动线设计', '50-100㎡', ['ins风', '卡通童趣'], ['游戏区'], true),
  designCase('demo-k3', '连锁母婴生活馆标准店', '200㎡+', ['简约现代'], ['母婴生活馆'], true),
  designCase('demo-k4', '婴童游泳馆空间方案', '100-200㎡', ['简约现代'], ['婴童游泳馆'], true),
  designCase('demo-k5', '童趣儿童乐园主题店', '200㎡+', ['卡通童趣'], ['儿童乐园'], false),
  designCase('demo-k6', '自然原木系亲子空间', '50-100㎡', ['自然原木'], ['儿童房'], false),
]

/** 形状对齐 GET /promotions/active 的返回 */
export const DEMO_PROMOTIONS = [
  { id: 'demo-a1', title: '春季订货会 · 全场满减', type: 'full_reduction',
    rules: { threshold: 500000, reduce: 80000 } },
  { id: 'demo-a2', title: '奶粉纸尿裤专享折扣', type: 'discount',
    rules: { rate: 0.85 } },
  { id: 'demo-a3', title: '新品首发 · 连体衣限时价', type: 'flash_sale',
    rules: { price: 3200, limit_qty: 500 } },
]

export const DEMO_QUICK_QUESTIONS = [
  '起订量是多少？',
  '多久能发货？',
  '可以定制 LOGO 吗？',
]
