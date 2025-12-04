from django.db import migrations


TRIGGER_STATEMENTS = [
    # Totales de citas antes de insertar
    (
        "tr_citas_calc_total_bi",
        """
        CREATE TRIGGER tr_citas_calc_total_bi
        BEFORE INSERT ON citas
        FOR EACH ROW
        BEGIN
            DECLARE s1 INT DEFAULT 0;
            DECLARE s2 INT DEFAULT 0;
            DECLARE s3 INT DEFAULT 0;

            SELECT COALESCE(MAX(precio), 0) INTO s1 FROM servicios WHERE id_servicio = NEW.servicio1;
            SELECT COALESCE(MAX(precio), 0) INTO s2 FROM servicios WHERE id_servicio = NEW.servicio2;
            SELECT COALESCE(MAX(precio), 0) INTO s3 FROM servicios WHERE id_servicio = NEW.servicio3;

            SET NEW.total = s1 + s2 + s3;
        END;
        """,
    ),
    # Totales de citas antes de actualizar
    (
        "tr_citas_calc_total_bu",
        """
        CREATE TRIGGER tr_citas_calc_total_bu
        BEFORE UPDATE ON citas
        FOR EACH ROW
        BEGIN
            DECLARE s1 INT DEFAULT 0;
            DECLARE s2 INT DEFAULT 0;
            DECLARE s3 INT DEFAULT 0;

            SELECT COALESCE(MAX(precio), 0) INTO s1 FROM servicios WHERE id_servicio = NEW.servicio1;
            SELECT COALESCE(MAX(precio), 0) INTO s2 FROM servicios WHERE id_servicio = NEW.servicio2;
            SELECT COALESCE(MAX(precio), 0) INTO s3 FROM servicios WHERE id_servicio = NEW.servicio3;

            SET NEW.total = s1 + s2 + s3;
        END;
        """,
    ),
    # Sincronizar resultados después de insertar cita
    (
        "tr_resultados_sync_ai",
        """
        CREATE TRIGGER tr_resultados_sync_ai
        AFTER INSERT ON citas
        FOR EACH ROW
        BEGIN
            DECLARE v_id CHAR(10);
            SET v_id = SUBSTRING(REPLACE(UUID(), '-', ''), 1, 10);

            INSERT INTO resultados (id_resultado, id_barbero, id_cita, total)
            VALUES (v_id, NEW.id_barbero, NEW.id_cita, NEW.total);
        END;
        """,
    ),
    # Sincronizar resultados después de actualizar cita
    (
        "tr_resultados_sync_au",
        """
        CREATE TRIGGER tr_resultados_sync_au
        AFTER UPDATE ON citas
        FOR EACH ROW
        BEGIN
            DECLARE existing_count INT DEFAULT 0;
            DECLARE v_id CHAR(10);

            SELECT COUNT(*) INTO existing_count FROM resultados WHERE id_cita = NEW.id_cita;

            IF existing_count > 0 THEN
                UPDATE resultados
                SET id_barbero = NEW.id_barbero,
                    total = NEW.total
                WHERE id_cita = NEW.id_cita;
            ELSE
                SET v_id = SUBSTRING(REPLACE(UUID(), '-', ''), 1, 10);
                INSERT INTO resultados (id_resultado, id_barbero, id_cita, total)
                VALUES (v_id, NEW.id_barbero, NEW.id_cita, NEW.total);
            END IF;
        END;
        """,
    ),
    # Sincronizar resultados después de eliminar cita
    (
        "tr_resultados_sync_ad",
        """
        CREATE TRIGGER tr_resultados_sync_ad
        AFTER DELETE ON citas
        FOR EACH ROW
        BEGIN
            DELETE FROM resultados WHERE id_cita = OLD.id_cita;
        END;
        """,
    ),
]


def create_triggers(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    for name, sql in TRIGGER_STATEMENTS:
        cursor.execute(f"DROP TRIGGER IF EXISTS {name}")
        cursor.execute(sql)


def drop_triggers(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    for name, _ in TRIGGER_STATEMENTS:
        cursor.execute(f"DROP TRIGGER IF EXISTS {name}")


class Migration(migrations.Migration):
    dependencies = [
        ('barberia', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_triggers, drop_triggers),
    ]
