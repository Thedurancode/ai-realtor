"""replace_property_status_pipeline

Revision ID: c8d2e4f5a7b9
Revises: b6f019cb8163
Create Date: 2026-02-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8d2e4f5a7b9'
down_revision: Union[str, None] = 'b6f019cb8163'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Old → New status mapping
STATUS_MAP = {
    'available': 'new_property',
    'pending': 'waiting_for_contracts',
    'sold': 'complete',
    'rented': 'complete',
    'off_market': 'new_property',
}

OLD_VALUES = ('available', 'pending', 'sold', 'rented', 'off_market')
NEW_VALUES = ('new_property', 'enriched', 'researched', 'waiting_for_contracts', 'complete')


def upgrade() -> None:
    # 1. Convert column to VARCHAR to decouple from enum type
    op.alter_column('properties', 'status',
                    type_=sa.String(30),
                    existing_type=sa.Enum(*OLD_VALUES, name='propertystatus'),
                    postgresql_using='status::text')

    # 2. Normalize to lowercase first (handles mixed-case values like 'PENDING')
    op.execute(sa.text("UPDATE properties SET status = TRIM(LOWER(status))"))

    # 3. Handle any NULL values by setting default
    op.execute(sa.text("UPDATE properties SET status = 'new_property' WHERE status IS NULL"))

    # 4. Map old values to new values
    for old_val, new_val in STATUS_MAP.items():
        op.execute(
            sa.text(f"UPDATE properties SET status = '{new_val}' WHERE status = '{old_val}'")
        )

    # 5. Catch-all: any unmapped values default to new_property
    op.execute(sa.text(
        "UPDATE properties SET status = 'new_property' "
        "WHERE status NOT IN ('new_property','enriched','researched','waiting_for_contracts','complete')"
    ))

    # 6. Verify all statuses are valid before creating enum
    op.execute(sa.text(
        "UPDATE properties SET status = 'new_property' "
        "WHERE status IS NULL OR status = ''"
    ))

    # 7. Drop old enum type
    op.execute(sa.text("DROP TYPE IF EXISTS propertystatus"))

    # 8. Create new enum type
    new_enum = sa.Enum(*NEW_VALUES, name='propertystatus')
    new_enum.create(op.get_bind(), checkfirst=True)

    # 9. Convert column back to enum
    op.alter_column('properties', 'status',
                    type_=sa.Enum(*NEW_VALUES, name='propertystatus'),
                    existing_type=sa.String(30),
                    postgresql_using='status::propertystatus',
                    server_default='new_property')


def downgrade() -> None:
    # Reverse mapping
    REVERSE_MAP = {
        'new_property': 'available',
        'enriched': 'available',
        'researched': 'pending',
        'waiting_for_contracts': 'pending',
        'complete': 'sold',
    }

    # 1. Convert to VARCHAR
    op.alter_column('properties', 'status',
                    type_=sa.String(30),
                    existing_type=sa.Enum(*NEW_VALUES, name='propertystatus'),
                    postgresql_using='status::text')

    # 2. Map new values back to old values
    for new_val, old_val in REVERSE_MAP.items():
        op.execute(
            sa.text(f"UPDATE properties SET status = '{old_val}' WHERE status = '{new_val}'")
        )

    # 3. Drop new enum type
    op.execute(sa.text("DROP TYPE IF EXISTS propertystatus"))

    # 4. Recreate old enum type
    old_enum = sa.Enum(*OLD_VALUES, name='propertystatus')
    old_enum.create(op.get_bind(), checkfirst=True)

    # 5. Convert column back to old enum
    op.alter_column('properties', 'status',
                    type_=sa.Enum(*OLD_VALUES, name='propertystatus'),
                    existing_type=sa.String(30),
                    postgresql_using='status::propertystatus',
                    server_default='available')
