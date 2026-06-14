"""Baseline: schema applied via db/schema/001_core_schema.sql.

After running that SQL file on a fresh database, stamp this revision:

    alembic stamp head

Future schema changes should add new revisions with upgrade()/downgrade().
"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "0001_baseline"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op: tables created by 001_core_schema.sql."""
    pass


def downgrade() -> None:
    """Baseline is not reversed automatically; restore from backup if needed."""
    pass
