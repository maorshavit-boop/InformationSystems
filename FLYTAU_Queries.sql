USE FLYTAU;

-- Find the average capacity of flights that occured
SELECT AVG(capacity)*100 AS avg_capacity_percentage 
FROM (
		SELECT F.flight_id, F.departure_date, (COUNT(FT.flight_id) / SUM(AC.columns_count * AC.rows_count)) AS capacity -- if airplane has 2 classes do I need to sum their number of seats
        FROM Flights F 
			LEFT JOIN Flight_Tickets FT ON F.flight_id = FT.flight_id
			JOIN Airplane_Classes AC ON F.airplane_id = AC.airplane_id
		WHERE F.status = 'Arrived'
        GROUP BY F.flight_id, F.departure_date
	) AS flights_capcity
;


SELECT A.size, A.manufacturer, T.class_type, SUM(T.price) AS total_revenue
FROM Flight_Tickets T
	JOIN Airplanes A ON T.airplane_id = A.airplane_id
	JOIN Orders O ON T.order_code = O.order_code 
WHERE O.status IN ('Active', 'Executed')      -- ensure order were not canceled
GROUP BY A.size, A.manufacturer, T.class_type
;


