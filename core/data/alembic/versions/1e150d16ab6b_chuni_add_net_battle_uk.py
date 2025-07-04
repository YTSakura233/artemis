"""chuni_add_net_battle_uk

Revision ID: 1e150d16ab6b
Revises: b23f985100ba
Create Date: 2024-06-21 22:57:18.418488

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '1e150d16ab6b'
down_revision = 'b23f985100ba'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'chuni_profile_net_battle', ['user'])
    # ### end Alembic commands ###


def downgrade():
    op.drop_constraint(None, 'chuni_profile_net_battle', type_='unique')
    # ### end Alembic commands ###
