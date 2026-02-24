-- Letter template query
-- Fetches letter recipient and content
-- Example: SELECT recipient_name, body, sender_name, footer FROM letters WHERE id = :letter_id

SELECT 'Aurélien Leno' AS RECIPIENT_NAME, 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.' AS BODY, 'Estelle Carotte' AS SENDER_NAME, 'Bon de commande' AS FORM_TITLE FROM DUAL
