-- Fix the logro_id column type in usuario_logro table
-- This changes the foreign key column from integer to varchar(50) to match the new primary key type of logro table

-- First, drop the existing foreign key constraint if it exists
ALTER TABLE usuario_logro DROP CONSTRAINT IF EXISTS usuario_logro_logro_id_fk;

-- Alter the column type
ALTER TABLE usuario_logro ALTER COLUMN logro_id TYPE varchar(50);

-- Add the foreign key constraint back
ALTER TABLE usuario_logro ADD CONSTRAINT usuario_logro_logro_id_fk FOREIGN KEY (logro_id) REFERENCES logro(codigo);
