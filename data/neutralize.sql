-- Limpia cualquier valor previo de entorno_pruebas por compañía
-- DELETE FROM ir_config_parameter
--  WHERE key LIKE 'fel.entorno_pruebas_%';

-- Inserta el valor True ('1') para cada compañía de la BD
INSERT INTO ir_config_parameter (key, value)
SELECT 'fel.entorno_pruebas_' || id::text, '1'
  FROM res_company
ON CONFLICT (key) DO UPDATE SET value = '1';
