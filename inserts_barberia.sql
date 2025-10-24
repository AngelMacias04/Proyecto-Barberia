USE Barberia;

-- 1) Pagos adicionales
INSERT INTO pagos (id_tipoDePago, tipoDePago) VALUES
('TARJETA',  'Tarjeta'),
('TRANSFER', 'Transferencia');

-- 2) Servicios adicionales
INSERT INTO servicios (id_servicio, servicio, precio) VALUES
('S002', 'Corte + Barba',        250),
('S003', 'Barba',                120),
('S004', 'Tintado',              300),
('S005', 'Afeitado clásico',     180),
('S006', 'Corte niño',           130);

-- 3) Barberos adicionales (referencian pagos)
INSERT INTO barbero (id_barbero, nombre, edad, telefono, tipoPago, user, password) VALUES
('B002', 'Ana Gómez',   '31', '5588887777', 'TARJETA',  'barbero2', 'abc123'),
('B003', 'Carlos Ruiz', '40', '5577776666', 'TRANSFER', 'barbero3', 'abc123');

-- 4) Clientes adicionales
INSERT INTO cliente (id_cliente, nombre, edad, telefono, user, password) VALUES
('C002', 'María Pérez', '30', '5550001111', 'cliente2', 'abc123'),
('C003', 'Jorge Díaz',  '35', '5550002222', 'cliente3', 'abc123'),
('C004', 'Sofía Lara',  '22', '5550003333', 'cliente4', 'abc123');

-- 5) Citas adicionales
-- (Comprueba totales: suman los precios de servicio1..3 que no son NULL)
INSERT INTO citas (id_cita, id_barbero, id_cliente, dia,        hora,   servicio1, servicio2, servicio3, total) VALUES
('CT0002', 'B001', 'C002', '2025-10-13', '16:00', 'S002',  NULL,   NULL,   250),  -- B001 con C002
('CT0003', 'B002', 'C001', '2025-10-14', '10:30', 'S001',  'S003', NULL,   270),  -- B002 con C001 (150 + 120)
('CT0004', 'B002', 'C003', '2025-10-14', '12:00', 'S005',  NULL,   NULL,   180),  -- B002 con C003
('CT0005', 'B003', 'C004', '2025-10-15', '09:00', 'S006',  'S003', NULL,   250),  -- B003 con C004 (130 + 120)
('CT0006', 'B003', 'C001', '2025-10-15', '11:00', 'S004',  NULL,   NULL,   300),  -- B003 con C001
('CT0007', 'B001', 'C004', '2025-10-16', '18:00', 'S001',  NULL,   NULL,   150);  -- B001 con C004

-- 6) Resultados adicionales (algunas citas ya atendidas)
INSERT INTO resultados (id_resultado, id_barbero, id_cita, total) VALUES
('R002', 'B001', 'CT0002', 250),
('R003', 'B002', 'CT0003', 270),
('R004', 'B002', 'CT0004', 180),
('R005', 'B003', 'CT0005', 250);

-- (CT0006 y CT0007 sin resultado aún -> sirven para probar que
-- un cliente/barbero puede ver sus citas aunque no tengan resultado)

-- 7) Dueño adicional (opcional)
INSERT INTO duenio (id_duenio, user, password, name) VALUES
('D002', 'admin2', 'admin456', 'Súper Admin');