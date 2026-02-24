-- Offers sub-report query
-- Fetches pricing offers with features
-- Example: SELECT offer_name, price, features FROM pricing_plans ORDER BY price

SELECT 'Offer #1' AS OFFER_NAME, 135 AS PRICE, 'Lorem ipsum dolor sit amet;Nullam at diam eget urna consequat;Sed fringilla quam at augue semper aliquam;Cras nec lacus eu turpis finibus vulputate' AS FEATURES FROM DUAL
UNION ALL
SELECT 'Offer #2', 175, 'Lorem ipsum dolor sit amet;Nullam at diam eget urna consequat;Sed fringilla quam at augue semper aliquam;Mauris viverra nulla vel semper mollis;Nulla quis massa eu urna suscipit vehicula;Curabitur a odio id risus pharetra iaculis' FROM DUAL
UNION ALL
SELECT 'Offer #3', 200, 'Lorem ipsum dolor sit amet;Nullam at diam eget urna consequat;Sed fringilla quam at augue semper aliquam;Mauris viverra nulla vel semper mollis;Cras nec lacus eu turpis finibus vulputate;Nulla quis massa eu urna suscipit vehicula;Curabitur a odio id risus pharetra iaculis' FROM DUAL
