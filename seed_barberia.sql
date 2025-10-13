USE Barberia;

-- 1) pagos (requerido por barbero.tipoPago)
INSERT INTO pagos (id_tipoDePago, tipoDePago)
VALUES ('EFECTIVO', 'Efectivo');

-- 2) servicios (requerido por citas.servicio1/2/3)
INSERT INTO servicios (id_servicio, servicio, precio)
VALUES ('S001', 'Corte básico', 150);

-- 3) barbero (referencia a pagos.tipoPago)
INSERT INTO barbero (id_barbero, nombre, edad, telefono, tipoPago, user, password)
VALUES ('B001', 'Juan Pérez', '28', '5512345678', 'EFECTIVO', 'barbero1', '123456');

-- 4) cliente
INSERT INTO cliente (id_cliente, nombre, edad, telefono, user, password)
VALUES ('C001', 'Luis López', '25', '5598765432', 'cliente1', '123456');

-- 5) citas (referencia a barbero, cliente, servicios)
INSERT INTO citas (id_cita, id_barbero, id_cliente, dia, hora, servicio1, servicio2, servicio3, total)
VALUES ('CT0001', 'B001', 'C001', '2025-10-12', '15:00', 'S001', NULL, NULL, 150);

-- 6) resultados (referencia a barbero y a la cita creada)
INSERT INTO resultados (id_resultado, id_barbero, id_cita, total)
VALUES ('R001', 'B001', 'CT0001', 150);

-- 7) duenio (tu usuario administrador)
INSERT INTO duenio (id_duenio, user, password, name)
VALUES ('D001', 'admin', 'admin123', 'Admin Barbería');