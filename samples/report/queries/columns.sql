-- Columns sub-report query
-- Fetches paragraphs of content for the multi-column text section
-- Example: SELECT content FROM report_paragraphs WHERE section = 'columns' ORDER BY sort_order

SELECT 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam volutpat faucibus vestibulum.' AS CONTENT FROM DUAL
UNION ALL
SELECT 'Phasellus id nisl nec arcu tempor ultricies non id tortor. Mauris ex nibh, viverra vitae nisi eget.' FROM DUAL
UNION ALL
SELECT 'Duis maximus mauris ac purus eleifend, sit amet blandit nulla lacinia.' FROM DUAL
