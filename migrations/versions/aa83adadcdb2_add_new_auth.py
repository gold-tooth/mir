"""add_new_auth

Revision ID: aa83adadcdb2
Revises: 84f11c7d251e
Create Date: 2024-02-06 09:10:05.547341

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aa83adadcdb2'
down_revision = '84f11c7d251e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('auth_user', 'hashed_password',
               existing_type=sa.VARCHAR(length=1024),
               type_=sa.LargeBinary(),
               existing_nullable=False,
               postgresql_using='hashed_password::bytea')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('auth_user', 'hashed_password',
               existing_type=sa.LargeBinary(),
               type_=sa.VARCHAR(length=1024),
               existing_nullable=False)
    # ### end Alembic commands ###
