"""add token usage json to prompt transform requests"""

from alembic import op
import sqlalchemy as sa


revision = "20260504_0006"
down_revision = "20260427_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("prompt_transform_requests", sa.Column("token_usage_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("prompt_transform_requests", "token_usage_json")
