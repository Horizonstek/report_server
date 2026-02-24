-- Invoice template query  
-- Fetches invoice line items
-- Example: SELECT description, price, quantity, (price * quantity) AS subtotal
-- FROM invoice_items WHERE invoice_id = :invoice_id

SELECT 'Website design' AS DESCRIPTION, 34.20 AS PRICE, 100 AS QUANTITY, 3420.00 AS SUBTOTAL FROM DUAL
UNION ALL
SELECT 'Website development', 45.50, 100, 4550.00 FROM DUAL
UNION ALL
SELECT 'Website integration', 25.75, 100, 2575.00 FROM DUAL
