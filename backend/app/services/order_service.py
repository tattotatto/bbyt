"""订单服务：创建订单、库存扣减、价格快照"""
import uuid
import random
import string
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import Product, ProductStatus
from app.models.user import User
from app.models.order import Order, OrderType, OrderStatus, PaymentStatus, PaymentMethod
from app.services.pricing import get_price


def generate_order_no() -> str:
    """生成唯一订单号: 时间戳 + 随机串"""
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d%H%M%S")
    rand = ''.join(random.choices(string.digits, k=6))
    return f"HX{ts}{rand}"


async def create_order(
    db: AsyncSession,
    retailer_id: uuid.UUID,
    items: list[dict],
    payment_method: str,
    remark: str | None = None,
    receiver_name: str | None = None,
    receiver_phone: str | None = None,
    receiver_address: str | None = None,
    store_design_detail: dict | None = None,
) -> Order:
    """创建订单：校验库存、匹配价格、生成快照、扣减库存"""

    # 1. 获取用户等级
    user_result = await db.execute(select(User).where(User.id == retailer_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise ValueError("用户不存在")

    level = user.level.value if hasattr(user.level, 'value') else str(user.level)

    # 2. 逐个校验商品、匹配价格
    validated_items = []
    total_amount = 0
    pricing_snapshot = {"level": level, "items": {}}
    has_virtual = False

    for item in items:
        product_id = uuid.UUID(item["product_id"])
        product_result = await db.execute(select(Product).where(Product.id == product_id))
        product = product_result.scalar_one_or_none()
        if not product:
            raise ValueError(f"商品 {item['product_id']} 不存在")
        if product.status != ProductStatus.ON_SALE:
            raise ValueError(f"商品 {product.name} 已下架")

        qty = item["qty"]

        if product.is_virtual:
            has_virtual = True
            # 虚拟商品：使用定价规则中 normal 的第一个阶梯价格
            normal_rules = product.pricing_rules.get("normal", [])
            if not normal_rules:
                raise ValueError(f"虚拟商品 {product.name} 未配置定价规则")
            unit_price = Decimal(str(normal_rules[0]["price"]))
            subtotal = unit_price * qty
        else:
            # 实物商品：检查库存
            if product.stock is not None and product.stock < qty:
                raise ValueError(f"商品 {product.name} 库存不足（剩余{product.stock}件）")

            # 匹配价格
            unit_price, _ = get_price(level, qty, product.pricing_rules)
            if unit_price is None:
                raise ValueError(f"商品 {product.name} 采购数量{qty}低于最低起批量{product.min_order_qty}")
            subtotal = unit_price * qty

            # 扣减库存
            if product.stock is not None:
                product.stock -= qty

        item_entry = {
            "product_id": str(product.id),
            "name": product.name,
            "qty": qty,
            "unit_price": float(unit_price),
            "subtotal": float(subtotal),
            "image": product.images[0] if product.images else None,
        }
        validated_items.append(item_entry)
        pricing_snapshot["items"][str(product.id)] = {
            "name": product.name,
            "qty": qty,
            "unit_price": float(unit_price),
            "pricing_rules": product.pricing_rules,
        }
        total_amount += int(subtotal * 100)  # 转为分

    # 3. 创建订单
    order = Order(
        order_no=generate_order_no(),
        type=OrderType.STORE_DESIGN if has_virtual else OrderType.PHYSICAL_GOODS,
        retailer_id=retailer_id,
        items=validated_items,
        total_amount=total_amount,
        pricing_snapshot=pricing_snapshot,
        payment_method=PaymentMethod(payment_method),
        payment_status=PaymentStatus.PENDING,
        status=OrderStatus.PENDING_PAYMENT,
        remark=remark,
        receiver_name=receiver_name,
        receiver_phone=receiver_phone,
        receiver_address=receiver_address,
        store_design_detail=store_design_detail,
        timeline=[{
            "status": "pending_payment",
            "time": datetime.now(timezone.utc).isoformat(),
            "operator": "system",
        }],
    )
    db.add(order)
    await db.flush()

    return order
