"""add_cart_address_history_favorites

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Add columns to existing tables ---
    op.add_column('products', sa.Column('sales_count', sa.Integer(), nullable=False, server_default='0', comment='销量'))
    op.add_column('users', sa.Column('nickname', sa.String(length=50), nullable=True, comment='用户昵称'))
    op.add_column('users', sa.Column('avatar', sa.String(length=500), nullable=True, comment='头像URL'))

    # --- Add REFUNDING to orderstatus enum ---
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'REFUNDING'")

    # --- cart_items ---
    op.create_table('cart_items',
        sa.Column('user_id', sa.Uuid(), nullable=False, comment='用户ID'),
        sa.Column('product_id', sa.Uuid(), nullable=False, comment='商品ID'),
        sa.Column('spec', sa.String(length=100), nullable=False, comment='规格'),
        sa.Column('quantity', sa.Integer(), nullable=False, comment='数量'),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'product_id', 'spec', name='uq_cart_user_product_spec'),
    )
    op.create_index(op.f('ix_cart_items_user_id'), 'cart_items', ['user_id'], unique=False)

    # --- addresses ---
    op.create_table('addresses',
        sa.Column('user_id', sa.Uuid(), nullable=False, comment='用户ID'),
        sa.Column('name', sa.String(length=50), nullable=False, comment='收货人姓名'),
        sa.Column('phone', sa.String(length=20), nullable=False, comment='收货人电话'),
        sa.Column('province', sa.String(length=20), nullable=False, comment='省'),
        sa.Column('city', sa.String(length=20), nullable=False, comment='市'),
        sa.Column('district', sa.String(length=20), nullable=False, comment='区'),
        sa.Column('detail', sa.String(length=200), nullable=False, comment='详细地址'),
        sa.Column('is_default', sa.Boolean(), nullable=False, comment='是否默认地址'),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_addresses_user_id'), 'addresses', ['user_id'], unique=False)

    # --- browse_histories ---
    op.create_table('browse_histories',
        sa.Column('user_id', sa.Uuid(), nullable=False, comment='用户ID'),
        sa.Column('product_id', sa.Uuid(), nullable=False, comment='商品ID'),
        sa.Column('viewed_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False, comment='最近浏览时间'),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'product_id', name='uq_history_user_product'),
    )
    op.create_index(op.f('ix_browse_histories_user_id'), 'browse_histories', ['user_id'], unique=False)

    # --- favorites ---
    op.create_table('favorites',
        sa.Column('user_id', sa.Uuid(), nullable=False, comment='用户ID'),
        sa.Column('product_id', sa.Uuid(), nullable=False, comment='商品ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'product_id', name='uq_favorite_user_product'),
    )
    op.create_index(op.f('ix_favorites_user_id'), 'favorites', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_favorites_user_id'), table_name='favorites')
    op.drop_table('favorites')
    op.drop_index(op.f('ix_browse_histories_user_id'), table_name='browse_histories')
    op.drop_table('browse_histories')
    op.drop_index(op.f('ix_addresses_user_id'), table_name='addresses')
    op.drop_table('addresses')
    op.drop_index(op.f('ix_cart_items_user_id'), table_name='cart_items')
    op.drop_table('cart_items')
    op.drop_column('users', 'avatar')
    op.drop_column('users', 'nickname')
    op.drop_column('products', 'sales_count')
