"""chuni_team_points

Revision ID: 745448d83696
Revises: 5ea363686347
Create Date: 2024-06-29 00:05:22.479187

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '745448d83696'
down_revision = '5ea363686347'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('chuni_profile_team', sa.Column('userTeamPoint', sa.JSON(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('chuni_profile_team', 'userTeamPoint')
    # ### end Alembic commands ###
