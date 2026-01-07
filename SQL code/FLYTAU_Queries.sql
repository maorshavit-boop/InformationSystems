USE FLYTAU;

-- ==========================================================
-- 1. Average Capacity of Executed Flights
-- ==========================================================
SELECT AVG(occupied_seats / total_seats) * 100 AS avg_capacity_percentage
FROM (
SELECT F.flight_id, F.departure_date,
        -- Count tickets sold for this flight (Comparing both ID and Date)
        (SELECT COUNT(*) 
         FROM Flight_Tickets FT 
         JOIN Orders O ON FT.order_code = O.order_code
         WHERE FT.flight_id = F.flight_id 
           AND FT.departure_date = F.departure_date 
           AND O.status IN ('Active', 'Executed')) AS occupied_seats,
         
        -- Calculate total physical seats in the plane (based on model)
        (SELECT SUM(rows_count * columns_count) 
         FROM Airplane_Classes AC 
         WHERE AC.airplane_id = F.airplane_id) AS total_seats
         
    FROM Flights F
    WHERE F.status = 'Arrived'
) AS flight_occupancy_data;


-- ==========================================================
-- 2. Revenue by Plane Size, Manufacturer, and Class
-- ==========================================================
SELECT A.size AS plane_size, A.manufacturer, FT.class_type, SUM(CIF.price) AS total_revenue -- Revenue calculated using the price from linking table
FROM Flight_Tickets FT
JOIN Orders O ON FT.order_code = O.order_code
JOIN Airplanes A ON FT.airplane_id = A.airplane_id
-- Join to pricing table using all 4 keys to get the correct historical price
JOIN Classes_In_Flights CIF 
    ON FT.flight_id = CIF.flight_id 
    AND FT.departure_date = CIF.departure_date 
    AND FT.class_type = CIF.class_type
    AND FT.airplane_id = CIF.airplane_id
WHERE O.status IN ('Active', 'Executed') 
GROUP BY A.size, A.manufacturer, FT.class_type
ORDER BY total_revenue DESC;

-- ==========================================================
-- 3. Cumulative Crew Hours (Pilots & Attendants Union)
-- ==========================================================
SELECT Employee_ID, First_Name, Last_Name,Role,
    -- Short flights (<= 6 hours / 360 minutes)
    ROUND(SUM(CASE WHEN flight_duration <= 360 THEN flight_duration ELSE 0 END) / 60, 2) AS Short_Flight_Hours,
    -- Long flights (> 360 minutes)
    ROUND(SUM(CASE WHEN flight_duration > 360 THEN flight_duration ELSE 0 END) / 60, 2) AS Long_Flight_Hours,
    -- Total hours
    ROUND(SUM(flight_duration) / 60, 2) AS Total_Hours
FROM (
    -- Part A: Pilots
    SELECT P.pilot_id AS Employee_ID, P.first_name, P.last_name, 'Pilot' AS Role, R.flight_duration
    FROM Pilots P
    JOIN Pilots_In_Flights PIF ON P.pilot_id = PIF.pilot_id
    -- Fix: Join using ID + Date
    JOIN Flights F ON PIF.flight_id = F.flight_id AND PIF.departure_date = F.departure_date 
    JOIN Flight_Routes R ON F.source_airport = R.source_airport AND F.destination_airport = R.destination_airport
    WHERE F.status = 'Arrived'
    
    UNION ALL

    -- Part B: Flight Attendants
    SELECT FA.attendant_id, FA.first_name, FA.last_name, 'Attendant' AS Role, R.flight_duration
    FROM Flight_Attendants FA
    JOIN Attendants_In_Flights AIF ON FA.attendant_id = AIF.attendant_id
    -- Fix: Join using ID + Date
    JOIN Flights F ON AIF.flight_id = F.flight_id AND AIF.departure_date = F.departure_date
    JOIN Flight_Routes R ON F.source_airport = R.source_airport AND F.destination_airport = R.destination_airport
    WHERE F.status = 'Arrived'
) AS All_Crew_Flights
GROUP BY Employee_ID, First_Name, Last_Name, Role;
 -- calculating only landed flights, and not current active flights. 

-- ==========================================================
-- 4. Monthly Order Cancellation Rate
-- ==========================================================
SELECT 
    DATE_FORMAT(order_date, '%Y-%m') AS order_month,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN status IN ('Cancelled by customer', 'Cancelled by system') THEN 1 ELSE 0 END) AS cancelled_orders,
    ROUND((SUM(CASE WHEN status IN ('Cancelled by customer', 'Cancelled by system') THEN 1 ELSE 0 END) / COUNT(*)) * 100, 2) AS cancellation_rate_percent
FROM Orders
GROUP BY DATE_FORMAT(order_date, '%Y-%m')
ORDER BY order_month;


-- ==========================================================
-- 5. Monthly Plane Activity Summary (Including Dominant Route)
-- ==========================================================
SELECT 
    Stats.airplane_id,
    Stats.activity_month,
    Stats.flights_executed,
    Stats.flights_cancelled,
    -- Utilization: Minutes in air / Total minutes in a 30-day month
    ROUND((Stats.total_flight_minutes / (30 * 24 * 60)) * 100, 2) AS utilization_percentage,
    
    -- Subquery to find the dominant route (most frequent)
    (SELECT CONCAT(source_airport, '-', destination_airport)
     FROM Flights F2
     WHERE F2.airplane_id = Stats.airplane_id 
       AND DATE_FORMAT(F2.departure_date, '%Y-%m') = Stats.activity_month
       AND F2.status = 'Arrived'
     GROUP BY source_airport, destination_airport
     ORDER BY COUNT(*) DESC
     LIMIT 1
    ) AS dominant_route

FROM (
    SELECT 
        F.airplane_id,
        DATE_FORMAT(F.departure_date, '%Y-%m') AS activity_month,
        SUM(CASE WHEN F.status = 'Arrived' THEN 1 ELSE 0 END) AS flights_executed,
        SUM(CASE WHEN F.status = 'Cancelled' THEN 1 ELSE 0 END) AS flights_cancelled,
        -- Sum minutes only for executed flights
        SUM(CASE WHEN F.status = 'Arrived' THEN R.flight_duration ELSE 0 END) AS total_flight_minutes
    FROM Flights F
    JOIN Flight_Routes R ON F.source_airport = R.source_airport AND F.destination_airport = R.destination_airport
    GROUP BY F.airplane_id, DATE_FORMAT(F.departure_date, '%Y-%m')
) AS Stats
ORDER BY Stats.airplane_id, Stats.activity_month;
