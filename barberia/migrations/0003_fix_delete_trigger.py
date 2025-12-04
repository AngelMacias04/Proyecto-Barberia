from django.db import migrations


CREATE_BEFORE_DELETE = """
CREATE TRIGGER tr_resultados_sync_bd
BEFORE DELETE ON citas
FOR EACH ROW
BEGIN
    DELETE FROM resultados WHERE id_cita = OLD.id_cita;
END;
"""

CREATE_AFTER_DELETE = """
CREATE TRIGGER tr_resultados_sync_ad
AFTER DELETE ON citas
FOR EACH ROW
BEGIN
    DELETE FROM resultados WHERE id_cita = OLD.id_cita;
END;
"""


def apply_trigger(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    cursor.execute("DROP TRIGGER IF EXISTS tr_resultados_sync_ad")
    cursor.execute("DROP TRIGGER IF EXISTS tr_resultados_sync_bd")
    cursor.execute(CREATE_BEFORE_DELETE)


def unapply_trigger(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    cursor.execute("DROP TRIGGER IF EXISTS tr_resultados_sync_bd")
    cursor.execute("DROP TRIGGER IF EXISTS tr_resultados_sync_ad")
    cursor.execute(CREATE_AFTER_DELETE)


class Migration(migrations.Migration):
    dependencies = [
        ('barberia', '0002_triggers'),
    ]

    operations = [
        migrations.RunPython(apply_trigger, unapply_trigger),
    ]
