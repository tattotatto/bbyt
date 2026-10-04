"""add_promotion_bill_knowledge

补建三张「模型有、迁移没有」的表：promotions / credit_bills / knowledge_entries。
在此之前生产库不存在这三张表，/promotions/active 返回 500。

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-10-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    """表已存在时跳过建表。

    存在的场景是真的：有人手工建过，或某个环境的表是用
    Base.metadata.create_all 建的。此时如果直接 create_table，
    deploy-prod.sh 里的 alembic upgrade head 会抛 DuplicateTable
    并中断整条部署流水线。
    """
    return sa.inspect(op.get_bind()).has_table(name)


def upgrade() -> None:
    # --- promotions ---
    if not _has_table('promotions'):
        op.create_table(
            'promotions',
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('type', sa.Enum('FULL_REDUCTION', 'DISCOUNT', 'FLASH_SALE', name='promotiontype'), nullable=False),
            sa.Column('rules', sa.JSON(), nullable=False, comment='促销规则'),
            sa.Column('product_ids', sa.JSON(), nullable=True, comment='适用商品ID列表(null=全场)'),
            sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
            sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )

    # --- credit_bills ---
    if not _has_table('credit_bills'):
        op.create_table(
            'credit_bills',
            sa.Column('retailer_id', sa.Uuid(), nullable=False, comment='用户ID'),
            sa.Column('bill_month', sa.String(length=7), nullable=False, comment='账单月份: 2026-07'),
            sa.Column('total_credit_used', sa.Integer(), nullable=False, comment='本期使用额度(分)'),
            sa.Column('total_repaid', sa.Integer(), nullable=False, comment='已还金额(分)'),
            sa.Column('status', sa.Enum('PENDING', 'PAID', 'OVERDUE', name='billstatus'), nullable=False),
            sa.Column('due_date', sa.String(length=10), nullable=True, comment='到期日'),
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.ForeignKeyConstraint(['retailer_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_credit_bills_retailer_id'), 'credit_bills', ['retailer_id'], unique=False)

    # --- knowledge_entries ---
    if not _has_table('knowledge_entries'):
        op.create_table(
            'knowledge_entries',
            sa.Column('source_type', sa.String(length=50), nullable=False, comment='来源: product|manual|faq|conversation'),
            sa.Column('source_id', sa.Uuid(), nullable=True, comment='关联商品ID'),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('content', sa.Text(), nullable=False, comment='知识内容（原始文本，用于全文搜索）'),
            sa.Column('embedding', sa.JSON(), nullable=True, comment='向量嵌入(1536维)，JSON存储兼容SQLite'),
            sa.Column('metadata', sa.JSON(), nullable=True, comment='元数据: 适龄、品类、认证等'),
            sa.Column('weight', sa.Float(), nullable=False, comment='权重（学习机制调整）'),
            sa.Column('status', sa.String(length=20), nullable=False, comment='active|deprecated'),
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.ForeignKeyConstraint(['source_id'], ['products.id'], ),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade() -> None:
    bind = op.get_bind()

    if _has_table('knowledge_entries'):
        op.drop_table('knowledge_entries')

    if _has_table('credit_bills'):
        op.drop_index(op.f('ix_credit_bills_retailer_id'), table_name='credit_bills')
        op.drop_table('credit_bills')

    if _has_table('promotions'):
        op.drop_table('promotions')

    # PostgreSQL 上 sa.Enum 会独立建类型，drop_table 不会带走它。
    # 不清理的话，重跑 upgrade head 会因为类型已存在而失败。
    # SQLite 没有原生枚举类型，跳过。
    if bind.dialect.name == 'postgresql':
        sa.Enum(name='promotiontype').drop(bind, checkfirst=True)
        sa.Enum(name='billstatus').drop(bind, checkfirst=True)
