"""initial

Revision ID: 0001
Revises: 
Create Date: 2025-06-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger, primary_key=True),
        sa.Column('username', sa.String(32)),
        sa.Column('full_name', sa.String(255)),
        sa.Column('rating', sa.Numeric(3,1), server_default='5.0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'))
    )


def downgrade() -> None:
    op.drop_table('users')
