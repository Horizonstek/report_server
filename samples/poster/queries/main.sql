-- Poster template query
-- Fetches event information for the poster
-- Example: SELECT event_name, event_date, venue_name, venue_city FROM events WHERE id = :event_id

SELECT 'e-sport live' AS EVENT_TYPE, 'Tournoi retro-gaming' AS EVENT_NAME, 'En live dans 50 villes de France' AS TAGLINE, 'Participez à la première édition près de chez vous' AS DESCRIPTION, '25 juin' AS EVENT_DATE, '2021' AS EVENT_YEAR, 'La souris verte' AS VENUE_NAME, 'Épinal' AS VENUE_CITY FROM DUAL
