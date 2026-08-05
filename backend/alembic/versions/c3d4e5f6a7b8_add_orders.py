"""add_orders

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-26 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('orders',
    sa.Column('order_no', sa.String(length=32), nullable=False, comment='订单号'),
    sa.Column('type', sa.Enum('PHYSICAL_GOODS', 'STORE_DESIGN', name='ordertype'), nullable=False),
    sa.Column('retailer_id', sa.Uuid(), nullable=False),
    sa.Column('items', sa.JSON(), nullable=False, comment='订单商品列表'),
    sa.Column('total_amount', sa.Integer(), nullable=False, comment='订单总额(分)'),
    sa.Column('pricing_snapshot', sa.JSON(), nullable=False, comment='下单时价格快照'),
    sa.Column('payment_method', sa.Enum('WECHAT_PAY', 'BANK_TRANSFER', 'CREDIT', name='paymentmethod'), nullable=True),
    sa.Column('payment_status', sa.Enum('PENDING', 'PAID', 'CONFIRMED', 'OVERDUE', name='paymentstatus'), nullable=False),
    sa.Column('payment_credit_used', sa.Integer(), nullable=False, server_default='0', comment='使用账期的金额(分)'),
    sa.Column('payment_evidence', sa.String(length=500), nullable=True, comment='银行转账凭证URL'),
    sa.Column('status', sa.Enum('PENDING_PAYMENT', 'PAID', 'SHIPPED', 'CONFIRMED', 'COMPLETED', 'CANCELLED', name='orderstatus'), nullable=False),
    sa.Column('remark', sa.Text(), nullable=True, comment='买家备注'),
    sa.Column('store_design_detail', sa.JSON(), nullable=True, comment='店面设计详情'),
    sa.Column('assigned_designer_id', sa.Uuid(), nullable=True, comment='指派设计师'),
    sa.Column('design_progress', sa.Enum('BRIEF', 'DRAFT', 'REVISION', 'FINALIZED', name='designprogress'), nullable=True),
    sa.Column('ai_conversation_id', sa.String(length=64), nullable=True, comment='AI对话记录引用(Phase 2)'),
    sa.Column('timeline', sa.JSON(), nullable=True, comment='状态变更时间线'),
    sa.Column('receiver_name', sa.String(length=50), nullable=True),
    sa.Column('receiver_phone', sa.String(length=20), nullable=True),
    sa.Column('receiver_address', sa.String(length=500), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['retailer_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['assigned_designer_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('order_no')
    )
    op.create_index(op.f('ix_orders_order_no'), 'orders', ['order_no'], unique=True)
    op.create_index(op.f('ix_orders_retailer_id'), 'orders', ['retailer_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_orders_retailer_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_order_no'), table_name='orders')
    op.drop_table('orders')
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS ordertype')
    op.execute('DROP TYPE IF EXISTS paymentmethod')
    op.execute('DROP TYPE IF EXISTS paymentstatus')
    op.execute('DROP TYPE IF EXISTS orderstatus')
    op.execute('DROP TYPE IF EXISTS designprogress')
