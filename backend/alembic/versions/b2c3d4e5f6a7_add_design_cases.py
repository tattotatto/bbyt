"""add_design_cases

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-26 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('design_cases',
    sa.Column('title', sa.String(length=200), nullable=False, comment='案例标题'),
    sa.Column('description', sa.Text(), nullable=True, comment='案例描述'),
    sa.Column('images', sa.JSON(), nullable=False, comment='案例图片URL列表(支持多张)'),
    sa.Column('category_tags', sa.JSON(), nullable=False, comment='分类标签: ["婴童游泳馆","母婴生活馆","儿童乐园"]'),
    sa.Column('style_tags', sa.JSON(), nullable=False, comment='风格标签: ["ins风","自然原木","卡通童趣"]'),
    sa.Column('store_area_range', sa.String(length=50), nullable=True, comment='面积范围: 50-100㎡/100-200㎡/200㎡+'),
    sa.Column('sort_order', sa.Integer(), nullable=False, comment='排序权重(越大越靠前)'),
    sa.Column('is_featured', sa.Boolean(), nullable=False, comment='是否精选(决定首页展示)'),
    sa.Column('status', sa.String(length=20), nullable=False, comment='published|draft'),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('design_cases')
