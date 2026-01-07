USE FLYTAU;

-- ==========================================================
-- Query 1: Average Capacity of Executed Flights
-- Objective: Calculate the average occupancy percentage for flights that successfully arrived.
-- Logic: (Occupied Seats / Total Physical Seats) * 100
-- ==========================================================
SELECT 
    AVG(occupied_seats / total_seats) * 100 AS avg_capacity_percentage
FROM (
    SELECT 
        F.flight_id,
        -- Count valid tickets sold for this specific flight (Active or Executed orders only)
        (SELECT COUNT(*) 
         FROM Flight_Tickets FT 
         JOIN Orders O ON FT.order_code = O.order_code
         WHERE FT.flight_id = F.flight_id 
         AND O.status IN ('Active', 'Executed')) AS occupied_seats,
         
        -- Calculate total physical capacity of the airplane (Sum of rows * columns for all classes)
        (SELECT SUM(rows_count * columns_count) 
         FROM Airplane_Classes AC 
         WHERE AC.airplane_id = F.airplane_id) AS total_seats
         
    FROM Flights F
    WHERE F.status = 'Arrived' -- Only consider flights that actually took place
) AS flight_occupancy_data;


-- ==========================================================
-- Query 2: Revenue Analysis by Plane Size, Manufacturer, and Class
-- Objective: Sum total revenue from ticket sales, grouped by aircraft attributes and cabin class.
-- ==========================================================
SELECT 
    A.size AS plane_size, 
    A.manufacturer, 
    FT.class_type, 
    SUM(FT.price) AS total_revenue
FROM Flight_Tickets FT
JOIN Orders O ON FT.order_code = O.order_code
JOIN Airplanes A ON FT.airplane_id = A.airplane_id
-- Ensure we only calculate revenue from valid orders (not cancelled ones)
WHERE O.status IN ('Active', 'Executed') 
GROUP BY A.size, A.manufacturer, FT.class_type
ORDER BY total_revenue DESC;


-- ==========================================================
-- Query 3: Cumulative Crew Flight Hours (Short vs. Long Haul)
-- Objective: Track total flight hours for each crew member, split by flight type (Short <= 6h, Long > 6h).
-- Logic: Unions Pilots and Flight Attendants into one dataset before aggregation.
-- ==========================================================
SELECT 
    Employee_ID,
    First_Name,
    Last_Name,
    Role,
    -- Sum duration for short flights (<= 360 mins) and convert to hours
    ROUND(SUM(CASE WHEN flight_duration <= 360 THEN flight_duration ELSE 0 END) / 60, 2) AS Short_Flight_Hours,
    -- Sum duration for long flights (> 360 mins) and convert to hours
    ROUND(SUM(CASE WHEN flight_duration > 360 THEN flight_duration ELSE 0 END) / 60, 2) AS Long_Flight_Hours,
    -- Total hours
    ROUND(SUM(flight_duration) / 60, 2) AS Total_Hours
FROM (
    -- Subquery 1: Fetch Pilot Data
    SELECT P.pilot_id AS Employee_ID, P.first_name, P.last_name, 'Pilot' AS Role, R.flight_duration
    FROM Pilots P
    JOIN Pilots_In_Flights PIF ON P.pilot_id = PIF.pilot_id
    JOIN Flights F ON PIF.flight_id = F.flight_id
    JOIN Flight_Routes R ON F.source_airport = R.source_airport AND F.destination_airport = R.destination_airport
    WHERE F.status = 'Arrived' -- Only count hours for flights that happened

    UNION ALL

    -- Subquery 2: Fetch Flight Attendant Data
    SELECT FA.attendant_id, FA.first_name, FA.last_name, 'Attendant' AS Role, R.flight_duration
    FROM Flight_Attendants FA
    JOIN Attendants_In_Flights AIF ON FA.attendant_id = AIF.attendant_id
    JOIN Flights F ON AIF.flight_id = F.flight_id
    JOIN Flight_Routes R ON F.source_airport = R.source_airport AND F.destination_airport = R.destination_airport
    WHERE F.status = 'Arrived'
) AS All_Crew_Flights
GROUP BY Employee_ID, First_Name, Last_Name, Role;


-- ==========================================================
-- Query 4: Monthly Order Cancellation Rate
-- Objective: Calculate the percentage of cancelled orders out of total orders per month.
-- ==========================================================
SELECT 
    DATE_FORMAT(order_date, '%Y-%m') AS order_month, -- Group by Year-Month
    COUNT(*) AS total_orders,
    -- Count orders that were cancelled either by the customer or the system
    SUM(CASE WHEN status IN ('Cancelled by customer', 'Cancelled by system') THEN 1 ELSE 0 END) AS cancelled_orders,
    
    -- Calculate percentage: (Cancelled / Total) * 100
    ROUND(
        (SUM(CASE WHEN status IN ('Cancelled by customer', 'Cancelled by system') THEN 1 ELSE 0 END) / COUNT(*)) * 100
    , 2) AS cancellation_rate_percent
FROM Orders
GROUP BY DATE_FORMAT(order_date, '%Y-%m')
ORDER BY order_month;


-- ==========================================================
-- Query 5: Monthly Aircraft Activity Summary
-- Objective: For each plane per month, show flights executed, cancelled, utilization %, and dominant route.
-- Note: Utilization assumes a standard 30-day month (43,200 minutes).
-- ==========================================================
SELECT 
    Stats.airplane_id,
    Stats.activity_month,
    Stats.flights_executed,
    Stats.flights_cancelled,
    -- Utilization: (Total Flight Minutes / Total Minutes in Month) * 100
    ROUND((Stats.total_flight_minutes / (30 * 24 * 60)) * 100, 2) AS utilization_percentage,
    
    -- Subquery to find the most frequent route (Source-Dest) for this plane in this month
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
        
        -- Count Arrived flights
        SUM(CASE WHEN F.status = 'Arrived' THEN 1 ELSE 0 END) AS flights_executed,
        
        -- Count Cancelled flights
        SUM(CASE WHEN F.status = 'Cancelled' THEN 1 ELSE 0 END) AS flights_cancelled,
        
        -- Sum flight duration only for executed flights
        SUM(CASE WHEN F.status = 'Arrived' THEN R.flight_duration ELSE 0 END) AS total_flight_minutes
        
    FROM Flights F
    JOIN Flight_Routes R ON F.source_airport = R.source_airport AND F.destination_airport = R.destination_airport
    GROUP BY F.airplane_id, DATE_FORMAT(F.departure_date, '%Y-%m')
) AS Stats
ORDER BY Stats.airplane_id, Stats.activity_month;