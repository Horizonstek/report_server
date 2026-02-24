-- Main report query
-- Fetches report metadata (cover page info)
-- Example: SELECT title, company_name, company_address, contact_email FROM report_config WHERE id = :report_id

SELECT 'Horizonstek Report' AS title, 'Horizonstek' AS company_name FROM DUAL
