"""mai2_presents

Revision ID: 5ea363686347
Revises: 680789dabab3
Create Date: 2024-06-28 14:49:07.666879

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '5ea363686347'
down_revision = '680789dabab3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('mai2_item_present',
    sa.Column('id', sa.BIGINT(), nullable=False),
    sa.Column('version', sa.INTEGER(), nullable=True),
    sa.Column('user', sa.Integer(), nullable=True),
    sa.Column('itemKind', sa.INTEGER(), nullable=False),
    sa.Column('itemId', sa.INTEGER(), nullable=False),
    sa.Column('stock', sa.INTEGER(), server_default='1', nullable=False),
    sa.Column('startDate', sa.TIMESTAMP(), nullable=True),
    sa.Column('endDate', sa.TIMESTAMP(), nullable=True),
    sa.ForeignKeyConstraint(['user'], ['aime_user.id'], onupdate='cascade', ondelete='cascade'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('version', 'user', 'itemKind', 'itemId', name='mai2_item_present_uk'),
    mysql_charset='utf8mb4'
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('mai2_item_present')
    # ### end Alembic commands ###
