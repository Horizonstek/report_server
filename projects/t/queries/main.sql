-- Ticket template query
-- Fetches passenger/ticket info
-- Example: SELECT passenger_name, flight, gate, seat, zone, departure_time, departure_date 
-- FROM tickets WHERE ticket_id = :ticket_id

SELECT 'Horizonstek' AS PASSENGER_NAME, 'DL31' AS FLIGHT, '29' AS GATE, '26E' AS SEAT, '4' AS ZONE, '5:10pm' AS DEPARTURE_TIME, 'Dec 15, 2018' AS DEPARTURE_DATE, 'CDG' AS ORIGIN, 'LFLL' AS DESTINATION, 'Coach' AS CLASS, '1257797706706' AS TICKET_NUMBER FROM DUAL
