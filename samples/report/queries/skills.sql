-- Skills sub-report query
-- Fetches feature cards for the skills showcase section
-- Example: SELECT feature_id, feature_name, feature_description FROM product_features ORDER BY sort_order

SELECT 'table-content' AS FEATURE_ID, 'Table of contents' AS FEATURE_NAME, 'Automatic table of contents with page numbers and clickable internal links.' AS FEATURE_DESCRIPTION FROM DUAL
UNION ALL
SELECT 'heading', 'Heading titles and page counters', 'Running headers and footers with page numbering.' FROM DUAL
UNION ALL
SELECT 'multi-columns', 'Multi-column text', 'CSS multi-column layout for professional text flow.' FROM DUAL
UNION ALL
SELECT 'internal-links', 'Internal links', 'Cross-references between pages with automatic page numbers.' FROM DUAL
UNION ALL
SELECT 'style', 'Different page types', 'Named pages with different margins, headers, and styles.' FROM DUAL
