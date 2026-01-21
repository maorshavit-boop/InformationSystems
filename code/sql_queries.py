# QUERY 1: Average Flight Occupancy
# Purpose: Calculates the average seat occupancy percentage for all flights that have successfully 'Arrived'.
# Logic:
#   1. Counts tickets sold per flight (Active or Executed orders).
#   2. Calculates total physical seats per airplane model.
#   3. Computes the ratio (Occupied / Total) and averages it across all flights.

q1 = """
SELECT AVG((occupied_seats * 100.0)/ total_seats)  AS avg_capacity_percentage
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
"""

# QUERY 2: Revenue Analysis by Aircraft & Class
# Purpose: Shows which aircraft models and seat classes generate the most revenue.
# Logic:
#   - Aggregates ticket prices grouped by Manufacturer, Plane Size, and Class Type.
#   - Includes revenue from 'Active', 'Executed', and 'Cancelled by customer' orders
#     (assuming cancellation fees are counted as revenue).

q2 = """
SELECT CONCAT(A.manufacturer, ' ', A.size, ' (', FT.class_type, ')') AS label, 
       SUM(FT.price) AS total_revenue
FROM Flight_Tickets FT
JOIN Orders O ON FT.order_code = O.order_code
JOIN Airplanes A ON FT.airplane_id = A.airplane_id
WHERE O.status IN ('Active', 'Executed', 'Cancelled by customer')
GROUP BY A.size, A.manufacturer, FT.class_type
ORDER BY total_revenue DESC
"""

# QUERY 3: Crew Workload Analysis (Flight Hours)
# Purpose: Tracks flight hours for Pilots and Flight Attendants, categorized by
# flight duration (Short vs. Long).
# Logic:
#   - Defines 'Short' as <= 6 hours (360 mins) and 'Long' as > 6 hours.
#   - Uses UNION ALL to combine data from Pilots and Flight Attendants tables.
#   - Only counts flights with status 'Arrived'.

q3 = """
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
"""

# QUERY 4: Monthly Order & Cancellation Trends
# Purpose: Monitors the volume of orders and the cancellation rate over time.
# Logic:
#   - Groups data by Year-Month.
#   - Counts total orders vs. cancelled orders (both by customer and system).
#   - Calculates the cancellation rate as a percentage.

q4 = """
 SELECT 
     DATE_FORMAT(order_date, '%Y-%m') AS order_month,
     COUNT(*) AS total_orders,
     SUM(CASE WHEN status IN ('Cancelled by customer', 'Cancelled by system') THEN 1 ELSE 0 END) AS cancelled_orders,
     ROUND((SUM(CASE WHEN status IN ('Cancelled by customer', 'Cancelled by system') THEN 1 ELSE 0 END) / COUNT(*)) * 100, 2) AS cancellation_rate_percent
 FROM Orders
 GROUP BY DATE_FORMAT(order_date, '%Y-%m')
 ORDER BY order_month;"""

# QUERY 5: Aircraft Utilization & Dominant Routes
# Purpose: Provides detailed operational stats per airplane per month.
# Logic:
# - Activity Month: Grouping by Year-Month.
# - Flights Executed/Cancelled: Simple counts based on status.
# - Utilization %: Calculated as (Distinct Days Flown / 30).
# - Dominant Route: Subquery to find the most frequent route flown by that specific plane in that specific month.

q5 = """
SELECT 
    Stats.airplane_id,
    Stats.activity_month,
    Stats.flights_executed,
    Stats.flights_cancelled,
     -- Utilization: Days flown / 30 days
    ROUND((Stats.days_flown / 30) * 100.0, 2) AS utilization_percentage,

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
         -- Count distinct days where the plane flew (status='Arrived')
         COUNT(DISTINCT CASE WHEN F.status = 'Arrived' THEN F.departure_date END) AS days_flown
     FROM Flights F
     -- Join is still kept to align with previous logic, though strictly not needed for days count
     JOIN Flight_Routes R ON F.source_airport = R.source_airport AND F.destination_airport = R.destination_airport
     GROUP BY F.airplane_id, DATE_FORMAT(F.departure_date, '%Y-%m')
 ) AS Stats
 ORDER BY Stats.airplane_id, Stats.activity_month; 
"""