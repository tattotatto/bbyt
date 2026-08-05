from fastapi import APIRouter
from app.api import auth, users, products, cases, orders, ai_ws, knowledge, credit, recommendations, dashboard, reports, promotions, upload, cart

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(products.router, prefix="/products", tags=["商品"])
api_router.include_router(cases.router, prefix="/cases", tags=["案例"])
api_router.include_router(orders.router, prefix="/orders", tags=["订单"])
api_router.include_router(ai_ws.router, prefix="/ai", tags=["AI助手"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["知识库"])
api_router.include_router(upload.router, prefix="/upload", tags=["上传"])
api_router.include_router(credit.router, prefix="/credit", tags=["账期"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["推荐"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["看板"])
api_router.include_router(reports.router, prefix="/reports", tags=["报表"])
api_router.include_router(promotions.router, prefix="/promotions", tags=["促销"])
api_router.include_router(cart.router, prefix="/cart", tags=["购物车"])
