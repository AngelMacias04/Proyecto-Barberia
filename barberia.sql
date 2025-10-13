-- Create the database (safe if it exists)
CREATE DATABASE IF NOT EXISTS Barberia;
USE Barberia;

-- Table: pagos
CREATE TABLE IF NOT EXISTS pagos (
    id_tipoDePago VARCHAR(10) PRIMARY KEY,
    tipoDePago VARCHAR(25)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table: barbero
CREATE TABLE IF NOT EXISTS barbero (
    id_barbero VARCHAR(10) PRIMARY KEY,
    nombre VARCHAR(50),
    edad VARCHAR(3),
    telefono VARCHAR(10),
    tipoPago VARCHAR(10),
    FOREIGN KEY (tipoPago) REFERENCES pagos (id_tipoDePago)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table: cliente
CREATE TABLE IF NOT EXISTS cliente (
    id_cliente VARCHAR(10) PRIMARY KEY,
    nombre VARCHAR(50),
    edad VARCHAR(3),
    telefono VARCHAR(10)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table: servicios
CREATE TABLE IF NOT EXISTS servicios (
    id_servicio VARCHAR(10) PRIMARY KEY,
    servicio VARCHAR(50),
    precio INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table: citas
CREATE TABLE IF NOT EXISTS citas (
    id_cita VARCHAR(20) NOT NULL PRIMARY KEY,
    id_barbero VARCHAR(10),
    id_cliente VARCHAR(10),
    dia VARCHAR(10),
    hora VARCHAR(6),
    servicio1 VARCHAR(10),
    servicio2 VARCHAR(10),
    servicio3 VARCHAR(10),
    total INT,
    FOREIGN KEY (id_barbero) REFERENCES barbero (id_barbero),
    FOREIGN KEY (id_cliente) REFERENCES cliente (id_cliente),
    FOREIGN KEY (servicio1) REFERENCES servicios (id_servicio),
    FOREIGN KEY (servicio2) REFERENCES servicios (id_servicio),
    FOREIGN KEY (servicio3) REFERENCES servicios (id_servicio)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table: resultados
CREATE TABLE IF NOT EXISTS resultados (
    id_resultado VARCHAR(10) PRIMARY KEY,
    id_barbero VARCHAR(10),
    id_cita VARCHAR(20),
    total INT,
    FOREIGN KEY (id_barbero) REFERENCES barbero (id_barbero),
    FOREIGN KEY (id_cita) REFERENCES citas (id_cita)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ===== second file contents merged below =====
-- Use the database
USE Barberia;

-- Add user and password columns to barbero
ALTER TABLE barbero
  ADD COLUMN user VARCHAR(15),
  ADD COLUMN password VARCHAR(10);

-- Add user and password columns to cliente
ALTER TABLE cliente
  ADD COLUMN user VARCHAR(15),
  ADD COLUMN password VARCHAR(10);

-- Create table: duenio
CREATE TABLE IF NOT EXISTS duenio (
    id_duenio VARCHAR(5) PRIMARY KEY,
    user VARCHAR(15),
    password VARCHAR(10),
    name VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;