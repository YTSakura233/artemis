"""chuni_fix_total_scores

Revision ID: 91c682918b67
Revises: 9c42e54a27fe
Create Date: 2025-03-29 11:19:46.063173

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '91c682918b67'
down_revision = '9c42e54a27fe'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('chuni_profile_data', 'totalMapNum',
               existing_type=mysql.INTEGER(display_width=11),
               type_=sa.BigInteger(),
               existing_nullable=True)
    op.alter_column('chuni_profile_data', 'totalHiScore',
               existing_type=mysql.INTEGER(display_width=11),
               type_=sa.BigInteger(),
               existing_nullable=True)
    op.alter_column('chuni_profile_data', 'totalBasicHighScore',
               existing_type=mysql.INTEGER(display_width=11),
               type_=sa.BigInteger(),
               existing_nullable=True)
    op.alter_column('chuni_profile_data', 'totalExpertHighScore',
               existing_type=mysql.INTEGER(display_width=11),
               type_=sa.BigInteger(),
               existing_nullable=True)
    op.alter_column('chuni_profile_data', 'totalMasterHighScore',
               existing_type=mysql.INTEGER(display_width=11),
               type_=sa.BigInteger(),
               existing_nullable=True)
    op.alter_column('chuni_profile_data', 'totalRepertoireCount',
               existing_type=mysql.INTEGER(display_width=11),
               type_=sa.BigInteger(),
               existing_nullable=True)
    op.alter_column('chuni_profile_data', 'totalAdvancedHighScore',
               existing_type=mysql.INTEGER(display_width=11),
               type_=sa.BigInteger(),
               existing_nullable=True)
    op.alter_column('chuni_profile_data', 'totalUltimaHighScore',
               existing_type=mysql.INTEGER(display_width=11),
               type_=sa.BigInteger(),
               existing_nullable=True,
               existing_server_default=sa.text("'0'"))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('chuni_profile_data', 'totalUltimaHighScore',
               existing_type=sa.BigInteger(),
               type_=mysql.INTEGER(display_width=11),
               existing_nullable=True,
               existing_server_default=sa.text("'0'"))
    op.alter_column('chuni_profile_data', 'totalAdvancedHighScore',
               existing_type=sa.BigInteger(),
               type_=mysql.INTEGER(display_width=11),
               existing_nullable=True)
    op.alter_column('chuni_profile_data', 'totalRepertoireCount',
               existing_type=sa.BigInteger(),
               type_=mysql.INTEGER(display_width=11),
               existing_nullable=True)
    op.alter_column('chuni_profile_data', 'totalMasterHighScore',
               existing_type=sa.BigInteger(),
               type_=mysql.INTEGER(display_width=11),
               existing_nullable=True)
    op.alter_column('chuni_profile_data', 'totalExpertHighScore',
               existing_type=sa.BigInteger(),
               type_=mysql.INTEGER(display_width=11),
               existing_nullable=True)
    op.alter_column('chuni_profile_data', 'totalBasicHighScore',
               existing_type=sa.BigInteger(),
               type_=mysql.INTEGER(display_width=11),
               existing_nullable=True)
    op.alter_column('chuni_profile_data', 'totalHiScore',
               existing_type=sa.BigInteger(),
               type_=mysql.INTEGER(display_width=11),
               existing_nullable=True)
    op.alter_column('chuni_profile_data', 'totalMapNum',
               existing_type=sa.BigInteger(),
               type_=mysql.INTEGER(display_width=11),
               existing_nullable=True)
    # ### end Alembic commands ###
