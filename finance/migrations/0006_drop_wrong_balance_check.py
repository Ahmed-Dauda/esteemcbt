from django.db import migrations


def drop_constraint_if_exists(apps, schema_editor):
    """
    Drop the mistaken CHECK (current_balance >= 0) constraint.

    - Postgres: uses ALTER TABLE ... DROP CONSTRAINT IF EXISTS.
    - SQLite:   no-op. SQLite silently ignores the constraint syntax anyway,
                and dev databases never had it applied.
    - Other:    no-op.
    """
    if schema_editor.connection.vendor != 'postgresql':
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            ALTER TABLE finance_financerecord
            DROP CONSTRAINT IF EXISTS finance_record_balance_check;
        """)


def restore_constraint(apps, schema_editor):
    """Reverse operation — re-add the constraint (only if ever rolled back)."""
    if schema_editor.connection.vendor != 'postgresql':
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            ALTER TABLE finance_financerecord
            ADD CONSTRAINT finance_record_balance_check
            CHECK (current_balance >= 0);
        """)


class Migration(migrations.Migration):
    """
    The ledger tracks debt — students with 'exhausted' status have a
    negative current_balance by design. The old CHECK (current_balance >= 0)
    made the schema inconsistent with the application logic and blocked
    imports of real data.
    """

    dependencies = [
        ('finance', '0005_alter_financerecord_total_deposit'),
    ]

    operations = [
        migrations.RunPython(drop_constraint_if_exists, restore_constraint),
    ]