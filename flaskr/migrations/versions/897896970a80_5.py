"""5

Revision ID: 897896970a80
Revises: a3029840bf43
Create Date: 2021-03-24 10:39:17.948460

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '897896970a80'
down_revision = 'a3029840bf43'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('order', sa.Column('courier_type', sa.String(length=5), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('order', 'courier_type')
    # ### end Alembic commands ###