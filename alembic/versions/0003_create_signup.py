from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    signup_status = pg.ENUM(
        "pending", "accepted", "declined",
        name="signupstatus",
        create_type=True,   # ← enum будет создан однократно
    )
    signup_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "signups",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "announcement_id",
            sa.Integer,
            sa.ForeignKey("announcements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("player_id", sa.BigInteger, nullable=False),
        sa.Column("role", sa.String, nullable=False),
        sa.Column(
            "status",
            pg.ENUM(
                "pending", "accepted", "declined",
                name="signupstatus",
                create_type=False,  # ← второй раз НЕ создаём
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("announcement_id", "player_id", name="uq_signups_announcement_player"),
    )


def downgrade() -> None:
    op.drop_table("signups")
    op.execute("DROP TYPE IF EXISTS signupstatus")
