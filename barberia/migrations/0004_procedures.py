from django.db import migrations


PROC_CREAR_CITA = """
CREATE PROCEDURE sp_crear_cita(
    IN p_barbero VARCHAR(10),
    IN p_cliente VARCHAR(10),
    IN p_dia VARCHAR(10),
    IN p_hora VARCHAR(6),
    IN p_serv1 VARCHAR(10),
    IN p_serv2 VARCHAR(10),
    IN p_serv3 VARCHAR(10)
)
BEGIN
    DECLARE v_count INT DEFAULT 0;
    DECLARE v_id VARCHAR(20);
    DECLARE s1 INT DEFAULT 0;
    DECLARE s2 INT DEFAULT 0;
    DECLARE s3 INT DEFAULT 0;
    DECLARE v_total INT DEFAULT 0;

    -- Validar disponibilidad (mismo barbero, día y hora)
    SELECT COUNT(*) INTO v_count
    FROM citas
    WHERE id_barbero = p_barbero
      AND dia = p_dia
      AND hora = p_hora;

    IF v_count > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'barbero_ocupado';
    END IF;

    -- Calcular total real por servicios seleccionados
    SELECT COALESCE(MAX(precio), 0) INTO s1 FROM servicios WHERE id_servicio = p_serv1;
    SELECT COALESCE(MAX(precio), 0) INTO s2 FROM servicios WHERE id_servicio = p_serv2;
    SELECT COALESCE(MAX(precio), 0) INTO s3 FROM servicios WHERE id_servicio = p_serv3;
    SET v_total = s1 + s2 + s3;

    -- Generar ID de cita
    SET v_id = CONCAT('CT', SUBSTRING(REPLACE(UUID(), '-', ''), 1, 18));

    -- Insertar cita
    INSERT INTO citas (id_cita, id_barbero, id_cliente, dia, hora, servicio1, servicio2, servicio3, total)
    VALUES (v_id, p_barbero, p_cliente, p_dia, p_hora, p_serv1, p_serv2, p_serv3, v_total);

    -- Resultado para el cliente
    SELECT v_id AS id_cita, v_total AS total_calculado;
END;
"""


PROC_TOP_SERVICIOS_CLIENTES = """
CREATE PROCEDURE sp_top_servicios_clientes(
    IN p_inicio DATE,
    IN p_fin DATE,
    IN p_limit INT
)
BEGIN
    -- Top servicios (considera servicio1/2/3)
    SELECT s.id_servicio,
           s.servicio,
           COUNT(*) AS usos,
           SUM(s.precio) AS total_estimado
    FROM (
        SELECT servicio1 AS servicio
        FROM citas
        WHERE servicio1 IS NOT NULL
          AND STR_TO_DATE(dia, '%Y-%m-%d') BETWEEN p_inicio AND p_fin
        UNION ALL
        SELECT servicio2 AS servicio
        FROM citas
        WHERE servicio2 IS NOT NULL
          AND STR_TO_DATE(dia, '%Y-%m-%d') BETWEEN p_inicio AND p_fin
        UNION ALL
        SELECT servicio3 AS servicio
        FROM citas
        WHERE servicio3 IS NOT NULL
          AND STR_TO_DATE(dia, '%Y-%m-%d') BETWEEN p_inicio AND p_fin
    ) t
    JOIN servicios s ON s.id_servicio = t.servicio
    GROUP BY s.id_servicio, s.servicio
    ORDER BY usos DESC, total_estimado DESC, s.id_servicio
    LIMIT p_limit;

    -- Top clientes por citas y gasto
    SELECT cl.id_cliente,
           cl.nombre,
           COUNT(*) AS citas,
           SUM(c.total) AS total_gastado
    FROM citas c
    JOIN cliente cl ON cl.id_cliente = c.id_cliente
    WHERE STR_TO_DATE(c.dia, '%Y-%m-%d') BETWEEN p_inicio AND p_fin
    GROUP BY cl.id_cliente, cl.nombre
    ORDER BY citas DESC, total_gastado DESC, cl.id_cliente
    LIMIT p_limit;
END;
"""


def create_procs(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    cursor.execute("DROP PROCEDURE IF EXISTS sp_crear_cita")
    cursor.execute("DROP PROCEDURE IF EXISTS sp_top_servicios_clientes")
    cursor.execute(PROC_CREAR_CITA)
    cursor.execute(PROC_TOP_SERVICIOS_CLIENTES)


def drop_procs(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    cursor.execute("DROP PROCEDURE IF EXISTS sp_crear_cita")
    cursor.execute("DROP PROCEDURE IF EXISTS sp_top_servicios_clientes")


class Migration(migrations.Migration):
    dependencies = [
        ('barberia', '0003_fix_delete_trigger'),
    ]

    operations = [
        migrations.RunPython(create_procs, drop_procs),
    ]
