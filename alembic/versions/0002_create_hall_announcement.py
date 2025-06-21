"""create hall & announcement tables"""

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.create_table(
        'halls',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(120), unique=True, nullable=False),
        sa.Column('address', sa.String(255))
    )
    op.create_table(
        'announcements',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('author_id', sa.BigInteger, sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('hall_id', sa.Integer, sa.ForeignKey('halls.id', ondelete='RESTRICT')),
        sa.Column('datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('players_need', sa.Integer, nullable=False),
        sa.Column('roles', sa.String(120)),
        sa.Column('balls_need', sa.Boolean, nullable=False),
        sa.Column('restrictions', sa.String(120)),
        sa.Column('is_paid', sa.Boolean, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

def downgrade() -> None:
    op.drop_table('announcements')
    op.drop_table('halls')
