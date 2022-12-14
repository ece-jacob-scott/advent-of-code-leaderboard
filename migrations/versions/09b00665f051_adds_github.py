"""adds github

Revision ID: 09b00665f051
Revises: 9bb34b4e5eb1
Create Date: 2022-12-13 17:55:29.426200

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '09b00665f051'
down_revision = '9bb34b4e5eb1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('github_access_token', sa.String(length=250), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('github_access_token')

    # ### end Alembic commands ###
