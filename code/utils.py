import random
import string
import datetime
from flask_login import UserMixin
import mysql.connector
from contextlib import contextmanager

# Configuration for database connection
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "root", # Updated to your requested password
    "database": "FLYTAU",
    "autocommit": True
}
#Context manager to handle database connection and cursor lifecycle.
@contextmanager
def db_cur():
    mydb = None
    cursor = None
    try:
        mydb = mysql.connector.connect(**db_config)
        cursor = mydb.cursor(dictionary=True)
        yield cursor
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        raise err
    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()


def register_new_customer(data):
    """
    Backend logic for user signup.
    Inserts data into Registered_Customers and Customer_Phones (supports multiple phones).
    """
    with db_cur() as cursor:
        try:
            # Check if email exists
            cursor.execute("SELECT email FROM Registered_Customers WHERE email = %s", (data['email'],))
            if cursor.fetchone():
                return False, "Email already registered."

            # Insert User Basic Info
            insert_cust = """
                INSERT INTO Registered_Customers 
                (email, first_name, middle_name, last_name, passport_num, registration_date, birth_date, password, customer_type)
                VALUES (%s, %s, %s, %s, %s, CURDATE(), %s, %s, 'Registered')
            """
            cursor.execute(insert_cust, (
                data['email'], data['first_name'], data.get('middle_name'),
                data['last_name'], data['passport_num'], data['birth_date'],
                data['password']
            ))

            # Insert Multiple Phones
            insert_phone = "INSERT INTO Customer_Phones (phone_num, email, customer_type) VALUES (%s, %s, 'Registered')"

            # Use the list we created in main.py
            phone_list = data.get('phones', [])

            # If for some reason it's a string (legacy support), make it a list
            if isinstance(phone_list, str):
                phone_list = [phone_list]

            for phone in phone_list:
                # Basic validation to ensure empty inputs aren't saved
                if phone and phone.strip():
                    cursor.execute(insert_phone, (phone.strip(), data['email']))

            return True, "Account created successfully!"

        except Exception as e:
            print(f"Signup error: {e}")
            return False, "An error occurred during registration."


def get_flights_with_filters(user_type, date=None, source=None, destination=None):
    """
returns fights by users filters
    """
    with db_cur() as cursor:
        if user_type == 'Manager':
            query = "SELECT * FROM Flights WHERE 1=1"
        else:
            query = "SELECT * FROM Flights WHERE status = 'Active'"

        params = []
        if date:
            query += " AND departure_date = %s"
            params.append(date)
        if source:
            query += " AND source_airport = %s"
            params.append(source)
        if destination:
            query += " AND destination_airport = %s"
            params.append(destination)

        cursor.execute(query, params)
        return cursor.fetchall()


from datetime import datetime, timedelta


def get_customer_history(email, status_filter=None):
    """
    Returns all orders for a specific user, filtered by status if provided.
    """
    with db_cur() as cursor:
        query = """
            SELECT O.order_code, 
                   O.status, 
                   O.order_date, 
                   F.flight_id,
                   F.source_airport,
                   F.destination_airport, 
                   F.departure_date, 
                   F.departure_time,
                   SUM(FT.price) as total_price, 
                   COUNT(FT.row_num) as ticket_count
            FROM Orders O
            JOIN Flight_Tickets FT ON O.order_code = FT.order_code
            JOIN Flights F ON FT.flight_id = F.flight_id
            WHERE O.customer_email = %s 
        """
        params = [email]

        # Add Status Filter Logic
        if status_filter and status_filter != 'All':
            if status_filter == 'Cancelled':
                query += " AND O.status LIKE 'Cancelled%'"  # Covers both 'Cancelled by system/customer'
            else:
                query += " AND O.status = %s"
                params.append(status_filter)

        query += """
            GROUP BY O.order_code, O.status, O.order_date, F.flight_id, 
                     F.source_airport, F.destination_airport, F.departure_date, F.departure_time
            ORDER BY O.order_date DESC
        """

        cursor.execute(query, tuple(params))
        return cursor.fetchall()


def get_order_by_code(order_code, email):
    """
    Fetches the total order details and all associated tickets.
    Returns a dictionary with 'info' (order data) and 'tickets' (list of tickets).
    """
    with db_cur() as cursor:
        query_order = """
            SELECT o.order_code, o.status, o.order_date, SUM(t.price) as total_price
            FROM Orders o
            JOIN Flight_Tickets t ON o.order_code = t.order_code
            WHERE o.order_code = %s AND o.customer_email = %s
            GROUP BY o.order_code
        """
        cursor.execute(query_order, (order_code, email))
        order_info = cursor.fetchone()

        if not order_info:
            return None

        query_tickets = """
            SELECT t.flight_id, t.row_num, t.column_num, t.class_type, t.price,
                   f.departure_date, f.departure_time, f.source_airport, f.destination_airport
            FROM Flight_Tickets t
            JOIN Flights f ON t.flight_id = f.flight_id
            WHERE t.order_code = %s
        """
        cursor.execute(query_tickets, (order_code,))
        tickets = cursor.fetchall()

        return {
            'info': order_info,
            'tickets': tickets
        }

def cancel_order_transaction(order_code):
    """
    Executes order cancellation:
    1. Checks if more than 36 hours remain before the flight.
    2. Calculates a 5% cancellation fee.
    3. Updates the order status and ticket prices in the DB.
    """
    with db_cur() as cursor:
        query_check = """
            SELECT F.departure_date, F.departure_time, SUM(FT.price) as current_total
            FROM Orders O
            JOIN Flight_Tickets FT ON O.order_code = FT.order_code
            JOIN Flights F ON FT.flight_id = F.flight_id
            WHERE O.order_code = %s
            GROUP BY F.departure_date, F.departure_time
        """
        cursor.execute(query_check, (order_code,))
        res = cursor.fetchone()
        
        if not res:
            return False, "Order not found."
        flight_dt = datetime.combine(res['departure_date'], (datetime.min + res['departure_time']).time())
        limit_time = datetime.now() + timedelta(hours=36)
        if limit_time > flight_dt:
            return False, "Cancellation is only allowed up to 36 hours before the flight."
        original_price = float(res['current_total'])
        cancellation_fee = original_price * 0.05
        
        try:
            cursor.execute("UPDATE Orders SET status = 'Cancelled by customer' WHERE order_code = %s", (order_code,))
            cursor.execute("""
                UPDATE Flight_Tickets 
                SET price = %s / (SELECT count FROM (SELECT COUNT(*) as count FROM Flight_Tickets WHERE order_code = %s) as tmp)
                WHERE order_code = %s
            """, (cancellation_fee, order_code, order_code))
            
            return True, f"Order cancelled. You were charged a 5% fee (${cancellation_fee:.2f})."
            
        except Exception as e:
            return False, f"Database error: {e}"


def get_flight_details(flight_id):
    """Retrieves basic flight info for the booking header."""
    with db_cur() as cursor:
        query = "SELECT * FROM Flights WHERE flight_id = %s"
        cursor.execute(query, (flight_id,))
        return cursor.fetchone()

def get_seats_for_flight(flight_id):
    """
    Retrieves all seats for the airplane assigned to this flight
    and checks if they are already occupied.
    """
    with db_cur() as cursor:
        cursor.execute("SELECT airplane_id FROM Flights WHERE flight_id = %s", (flight_id,))
        flight = cursor.fetchone()
        if not flight: return []
        query = """
            SELECT s.row_num, s.column_num, s.class_type,
                   CASE WHEN t.order_code IS NOT NULL THEN 1 ELSE 0 END AS is_taken
            FROM Seats s
            LEFT JOIN Flight_Tickets t 
                ON s.row_num = t.row_num 
                AND s.column_num = t.column_num 
                AND s.airplane_id = t.airplane_id
                AND t.flight_id = %s
            WHERE s.airplane_id = %s
            ORDER BY s.class_type, s.row_num, s.column_num
        """
        cursor.execute(query, (flight_id, flight['airplane_id']))
        return cursor.fetchall()


def get_flight_seat_map(flight_id):
    """
    Fetches seats and organizes them by ROW to fix visual grid alignment issues.
    Returns a dictionary structure: { row_num: { col_num: seat_object } }
    """
    with db_cur() as cursor:
        # 1. Fetch flight info
        query_flight = """
            SELECT f.*, a.airplane_id, a.size 
            FROM Flights f 
            JOIN Airplanes a ON f.airplane_id = a.airplane_id 
            WHERE f.flight_id = %s
        """
        cursor.execute(query_flight, (flight_id,))
        flight = cursor.fetchone()
        if not flight: return None, {}

        # 2. Fetch all seats + Occupancy status
        query_seats = """
            SELECT s.row_num, s.column_num, s.class_type, s.airplane_id,
                   CASE WHEN t.order_code IS NOT NULL THEN 1 ELSE 0 END AS is_taken
            FROM Seats s
            LEFT JOIN Flight_Tickets t 
                ON s.row_num = t.row_num 
                AND s.column_num = t.column_num 
                AND s.airplane_id = t.airplane_id
                AND t.flight_id = %s
                AND t.departure_date = %s
            WHERE s.airplane_id = %s
            ORDER BY s.row_num, s.column_num
        """
        cursor.execute(query_seats, (flight_id, flight['departure_date'], flight['airplane_id']))
        raw_seats = cursor.fetchall()

        # 3. Reorganize into a structured map: rows[row_num][col_num] = seat
        # This allows the HTML to iterate 1-6 explicitly and handle gaps.
        seat_map = {}
        max_row = 0

        for seat in raw_seats:
            r = seat['row_num']
            c = seat['column_num']
            if r not in seat_map:
                seat_map[r] = {}
            seat_map[r][c] = seat
            if r > max_row: max_row = r

        return flight, {'map': seat_map, 'max_row': max_row}


MANAGER_PRICES = {}


def get_current_price(flight_id, class_type):
    """
    Retrieves the price for a specific flight and class directly from the database.
    Raises an error if no price is found, preventing 'free' tickets.
    """
    with db_cur() as cursor:
        query = """
            SELECT cif.price 
            FROM Classes_In_Flights cif
            JOIN Flights f ON cif.flight_id = f.flight_id 
                          AND cif.departure_date = f.departure_date
            WHERE cif.flight_id = %s AND cif.class_type = %s
        """
        cursor.execute(query, (flight_id, class_type))
        result = cursor.fetchone()

        if result:
            return float(result['price'])

        # Raise an error to stop execution immediately if data is missing
        raise ValueError(f"CRITICAL: No price set for Flight {flight_id} in {class_type} class. Please choose a different ticket")


#Creates a booking
def create_booking(flight_id, selected_seats, user, guest_data=None):
    """
    Updated to support the new schema:
    1. Fetches price from Classes_In_Flights.
    2. Uses departure_date as part of the primary key for Flight_Tickets.
    3. Handles guest phone number storage.
    """
    with db_cur() as cursor:
        try:
            # 1. Fetch Flight Departure Date (Required for keys)
            cursor.execute("SELECT departure_date FROM Flights WHERE flight_id = %s", (flight_id,))
            res = cursor.fetchone()
            if not res:
                return False, "Flight not found", None
            departure_date = res['departure_date']

            # 2. Generate Order Code
            order_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

            # 3. Handle Customer
            if user.is_authenticated:
                email = user.id
                customer_type = 'Registered'
            else:
                email = guest_data['email']
                customer_type = 'Unregistered'

                # Check if guest exists, if not create them
                cursor.execute("SELECT email FROM Unregistered_Customers WHERE email = %s", (email,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO Unregistered_Customers (email, first_name, middle_name, last_name, customer_type)
                        VALUES (%s, %s, %s, %s, 'Unregistered')
                    """, (email, guest_data['first_name'], guest_data.get('middle_name'), guest_data['last_name']))

                # --- FIX: Save Guest Phone Number ---
                guest_phone = guest_data.get('phone')
                if guest_phone:
                    # We use INSERT IGNORE because phone_num is a Primary Key.
                    # If the number already exists, we skip it to prevent a crash.
                    cursor.execute("""
                        INSERT IGNORE INTO Customer_Phones (phone_num, email, customer_type)
                        VALUES (%s, %s, 'Unregistered')
                    """, (guest_phone, email))

            # 4. Create Order
            cursor.execute("""
                INSERT INTO Orders (order_code, customer_email, status, order_date, customer_type)
                VALUES (%s, %s, 'Active', CURDATE(), %s)
            """, (order_code, email, customer_type))

            # 5. Process Tickets
            for seat_key in selected_seats:
                # Format: "row-col-class-airplane_id"
                parts = seat_key.split('-')
                row = parts[0]
                col = parts[1]
                s_class = parts[2]
                airplane_id = "-".join(parts[3:])

                # Verify Price exists (Validation step)
                cursor.execute("""
                    SELECT price FROM Classes_In_Flights 
                    WHERE flight_id = %s AND departure_date = %s AND class_type = %s AND airplane_id = %s
                """, (flight_id, departure_date, s_class, airplane_id))

                price_check = cursor.fetchone()
                if not price_check:
                    return False, f"Pricing not found for class {s_class}", None

                # Insert Ticket
                cursor.execute("""
                    INSERT INTO Flight_Tickets 
                    (order_code, flight_id, departure_date, row_num, column_num, class_type, airplane_id, price)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (order_code, flight_id, departure_date, row, col, s_class, airplane_id, price_check['price']))

            return True, "Booking successful!", order_code
        except Exception as e:
            print(f"Booking Error: {e}")
            return False, str(e), None
class Worker:
    """
    Base class for all employees (Pilots, Flight Attendants, Managers).
    """
    def __init__(self, first_name, middle_name, last_name, city, street, house_num, start_date):
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name
        self.city = city
        self.street = street
        self.house_num = house_num
        self.start_date = start_date

    def get_full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    def get_address(self):
        return f"{self.street} {self.house_num}, {self.city}"


class Pilot(Worker):
    """
    Maps to 'Pilots' table.
    """
    def __init__(self, pilot_id, first_name, middle_name, last_name, city, street, house_num, start_date, long_flight_training):
        super().__init__(first_name, middle_name, last_name, city, street, house_num, start_date)
        self.id = pilot_id
        self.long_flight_training = True if long_flight_training else False

#Returns the workers role
    def get_role(self):
        return "Pilot"


class FlightAttendant(Worker):
    """
    Maps to 'Flight_Attendants' table.
    """
    def __init__(self, attendant_id, first_name, middle_name, last_name, city, street, house_num, start_date, long_flight_training):
        super().__init__(first_name, middle_name, last_name, city, street, house_num, start_date)
        self.id = attendant_id
        self.long_flight_training = True if long_flight_training else False

    # Returns the workers role
    def get_role(self):
        return "Flight Attendant"


class Manager(Worker, UserMixin):
    """
    Maps to 'Managers' table.
    Inherits from UserMixin to support Flask-Login.
    """
    def __init__(self, manager_id, password, first_name, middle_name, last_name, city, street, house_num, start_date):
        super().__init__(first_name, middle_name, last_name, city, street, house_num, start_date)
        self.id = manager_id
        self.password = password
        self.user_type = 'Manager'

    # Returns the workers role
    def get_role(self):
        return "Manager"

def get_all_pilots():
    """Fetches rows from Pilots table and converts them to Pilot objects."""
    pilots_list = []
    with db_cur() as cursor:
        cursor.execute("SELECT * FROM Pilots")
        results = cursor.fetchall()
        
        for row in results:
            p = Pilot(
                pilot_id=row['pilot_id'],
                first_name=row['first_name'],
                middle_name=row['middle_name'],
                last_name=row['last_name'],
                city=row['city'],
                street=row['street'],
                house_num=row['house_num'],
                start_date=row['start_date'],
                long_flight_training=row['long_flight_training']
            )
            pilots_list.append(p)
    return pilots_list

def get_all_attendants():
    """Fetches rows from Flight_Attendants table and converts to objects."""
    attendants_list = []
    with db_cur() as cursor:
        cursor.execute("SELECT * FROM Flight_Attendants")
        results = cursor.fetchall()
        
        for row in results:
            fa = FlightAttendant(
                attendant_id=row['attendant_id'],
                first_name=row['first_name'],
                middle_name=row['middle_name'],
                last_name=row['last_name'],
                city=row['city'],
                street=row['street'],
                house_num=row['house_num'],
                start_date=row['start_date'],
                long_flight_training=row['long_flight_training']
            )
            attendants_list.append(fa)
    return attendants_list

def get_all_managers(manager_id):
    """Fetches rows from Managers table and converts to objects."""
    with db_cur() as cursor:
        cursor.execute("SELECT * FROM Managers WHERE manager_id = %s", (manager_id,))
        row = cursor.fetchone()
        
        if row:
            return Manager(
                manager_id=row['manager_id'],
                first_name=row['first_name'],
                middle_name=row['middle_name'],
                last_name=row['last_name'],
                city=row['city'],
                street=row['street'],
                house_num=row['house_num'],
                start_date=row['start_date'],
                password=row['password']
            )
    return None

#NEED TO CHECK WHY ID AND EMAIL!!!
class User(UserMixin):
    """
Class that represents unregistered user table
    """
    def __init__(self, email, first_name, last_name, middle_name=None):
        self.id = email  
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.middle_name = middle_name
        self.user_type = 'Guest'
#Returns full name
    def get_full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"


class RegisteredUser(User):
    """
Class of registered users, inherits from user class
    """
    def __init__(self, email, first_name, last_name, passport_num, birth_date, password, registration_date, middle_name=None):
        super().__init__(email, first_name, last_name, middle_name)        
        self.passport_num = passport_num
        self.birth_date = birth_date
        self.password = password
        self.registration_date = registration_date
        self.user_type = 'Registered'

    # Open code/utils.py and add these imports if missing


from flask import flash


# Add these new functions at the bottom of utils.py

def get_all_resources():
    """
    Fetches resources needed for the Add Flight form:
    - Planes (to check size)
    - Pilots (to assign crew)
    - Attendants (to assign crew)
    - Routes (to check duration)
    """
    with db_cur() as cursor:
        cursor.execute("SELECT * FROM Airplanes")
        planes = cursor.fetchall()

        cursor.execute("SELECT * FROM Pilots")
        pilots = cursor.fetchall()

        cursor.execute("SELECT * FROM Flight_Attendants")
        attendants = cursor.fetchall()

        cursor.execute("SELECT source_airport, destination_airport, flight_duration FROM Flight_Routes")
        routes = cursor.fetchall()

    return planes, pilots, attendants, routes


# In code/utils.py

# In code/utils.py

# In code/utils.py



# Helper to check Runway Availability (15 min buffer)
def check_runway_conflict(date, time, runway):
    """
    Checks if runway is busy (15 min buffer).
    """
    with db_cur() as cursor:
        cursor.execute("""
            SELECT flight_id, departure_time FROM Flights 
            WHERE departure_date = %s 
              AND runway_num = %s 
              AND status != 'Cancelled'
              AND ABS(TIMESTAMPDIFF(MINUTE, departure_time, %s)) < 15
        """, (date, runway, time))
        conflict = cursor.fetchone()
        if conflict:
            return f"Runway Collision: Flight {conflict['flight_id']} is scheduled at {conflict['departure_time']}."
    return None


def get_available_resources(date, new_start_time, new_duration):
    """
    Returns resources NOT conflicting with the robust overlap logic.
    """
    is_long_haul = int(new_duration) > 360

    with db_cur() as cursor:
        # 1. AVAILABLE PLANES
        size_sql = "AND size = 'Big'" if is_long_haul else ""

        # We exclude planes that match the overlap criteria
        cursor.execute(f"""
            SELECT * FROM Airplanes 
            WHERE airplane_id NOT IN (
                SELECT f.airplane_id
                FROM Flights f
                JOIN Flight_Routes r ON f.source_airport = r.source_airport AND f.destination_airport = r.destination_airport
                WHERE f.departure_date = %s
                  AND f.status != 'Cancelled'
                  AND (
                      f.departure_time < ADDTIME(%s, SEC_TO_TIME((%s + 60)*60))
                      AND 
                      %s < ADDTIME(f.departure_time, SEC_TO_TIME((r.flight_duration + 60)*60))
                  )
            )
            {size_sql}
        """, (date, new_start_time, new_duration, new_start_time))
        planes = cursor.fetchall()

        # 2. AVAILABLE PILOTS (Simple day check)
        training_sql = "AND long_flight_training = 1" if is_long_haul else ""
        cursor.execute(f"""
            SELECT * FROM Pilots 
            WHERE pilot_id NOT IN (SELECT pilot_id FROM Pilots_In_Flights WHERE departure_date = %s)
            {training_sql}
        """, (date,))
        pilots = cursor.fetchall()

        # 3. AVAILABLE ATTENDANTS
        cursor.execute(f"""
            SELECT * FROM Flight_Attendants 
            WHERE attendant_id NOT IN (SELECT attendant_id FROM Attendants_In_Flights WHERE departure_date = %s)
            {training_sql}
        """, (date,))
        attendants = cursor.fetchall()

    return planes, pilots, attendants


def check_plane_availability(plane_id, date, time, duration):
    with db_cur() as cursor:
        cursor.execute("""
            SELECT flight_id, departure_time FROM Flights 
            WHERE departure_date = %s 
              AND airplane_id = %s
              AND status != 'Cancelled'
              AND ABS(TIMESTAMPDIFF(MINUTE, departure_time, %s)) < (%s + 60)
        """, (date, plane_id, time, duration))
        conflict = cursor.fetchone()
        if conflict:
            return f"Aircraft Conflict: Plane {plane_id} is already assigned to Flight {conflict['flight_id']}."
    return None
# In code/utils.py

def check_plane_availability(plane_id, date, new_start_time, new_duration):
    """
    Checks if a plane is busy by looking at BOTH the new flight's duration
    AND the existing flights' durations.
    """
    with db_cur() as cursor:
        # We need to JOIN Flight_Routes to know how long the EXISTING flights last.
        # Logic: Overlap exists if (StartA < EndB) AND (StartB < EndA)
        # End Times include a 60 minute buffer.

        cursor.execute("""
            SELECT f.flight_id, f.departure_time, r.flight_duration
            FROM Flights f
            JOIN Flight_Routes r ON f.source_airport = r.source_airport AND f.destination_airport = r.destination_airport
            WHERE f.departure_date = %s
              AND f.airplane_id = %s
              AND f.status != 'Cancelled'
              AND (
                  -- 1. The Existing Flight (f) starts BEFORE New Flight Ends
                  f.departure_time < ADDTIME(%s, SEC_TO_TIME((%s + 60)*60))
                  AND 
                  -- 2. The New Flight starts BEFORE Existing Flight (f) Ends
                  %s < ADDTIME(f.departure_time, SEC_TO_TIME((r.flight_duration + 60)*60))
              )
        """, (date, plane_id, new_start_time, new_duration, new_start_time))

        conflict = cursor.fetchone()
        if conflict:
            return f"Aircraft Conflict: Plane {plane_id} is busy with Flight {conflict['flight_id']}."
    return None

# Final Commit Function
def create_flight_final_step(form_data):
    f_id = form_data['flight_id']
    date = form_data['departure_date']
    time = form_data['departure_time']
    plane_id = form_data['airplane_id']
    source = form_data['source']
    dest = form_data['dest']
    runway = form_data['runway_num']
    duration = int(form_data['duration'])

    price_economy = form_data.get('price_economy')
    price_business = form_data.get('price_business')
    pilot_ids = form_data.getlist('pilots')
    attendant_ids = form_data.getlist('attendants')

    # FINAL SAFETY CHECKS
    if check_flight_id_exists(f_id):
        return False, f"CRITICAL: Flight ID {f_id} is already in use."

    if check_runway_conflict(date, time, runway):
        return False, "CRITICAL: Runway conflict detected."

    if check_plane_availability(plane_id, date, time, duration):
        return False, "CRITICAL: Aircraft conflict detected."

    with db_cur() as cursor:
        try:
            # 1. Get Plane Size
            cursor.execute("SELECT size FROM Airplanes WHERE airplane_id = %s", (plane_id,))
            res = cursor.fetchone()
            plane_size = res['size']

            # 2. Insert Flight
            cursor.execute("""
                INSERT INTO Flights (flight_id, departure_date, airplane_id, source_airport, destination_airport, status, departure_time, runway_num)
                VALUES (%s, %s, %s, %s, %s, 'Active', %s, %s)
            """, (f_id, date, plane_id, source, dest, time, runway))

            # 3. Insert Crew
            for pid in pilot_ids:
                cursor.execute(
                    "INSERT INTO Pilots_In_Flights (pilot_id, flight_id, departure_date) VALUES (%s, %s, %s)",
                    (pid, f_id, date))
            for aid in attendant_ids:
                cursor.execute(
                    "INSERT INTO Attendants_In_Flights (attendant_id, flight_id, departure_date) VALUES (%s, %s, %s)",
                    (aid, f_id, date))

            # 4. Insert Prices
            cursor.execute("""
                INSERT INTO Classes_In_Flights (flight_id, departure_date, class_type, airplane_id, price)
                VALUES (%s, %s, 'Economy', %s, %s)
            """, (f_id, date, plane_id, price_economy))

            # Only insert Business if plane is Big
            if plane_size == 'Big':
                if not price_business:
                    return False, "Business Price required for Big plane."
                cursor.execute("""
                    INSERT INTO Classes_In_Flights (flight_id, departure_date, class_type, airplane_id, price)
                    VALUES (%s, %s, 'Business', %s, %s)
                """, (f_id, date, plane_id, price_business))

            return True, "Flight Created Successfully!"
        except Exception as e:
            return False, f"Database Error: {str(e)}"
def check_flight_id_exists(flight_id):
    with db_cur() as cursor:
        cursor.execute("SELECT flight_id FROM Flights WHERE flight_id = %s", (flight_id,))
        if cursor.fetchone():
            return True
    return False

# ... (keep check_runway_conflict and get_available_resources as they were) ...

def create_flight_final_step(form_data):
    """
    Final Commit with DOUBLE-CHECK for ID uniqueness.
    """
    f_id = form_data['flight_id']

    # 1. FINAL SAFETY CHECK: Flight ID Uniqueness
    if check_flight_id_exists(f_id):
        return False, f"CRITICAL: Flight ID {f_id} was taken by another manager just now."

    # Extract rest of data
    date = form_data['departure_date']
    time = form_data['departure_time']
    plane_id = form_data['airplane_id']
    source = form_data['source']
    dest = form_data['dest']
    runway = form_data['runway_num']

    price_economy = form_data.get('price_economy')
    price_business = form_data.get('price_business')
    pilot_ids = form_data.getlist('pilots')
    attendant_ids = form_data.getlist('attendants')

    with db_cur() as cursor:
        try:
            # Insert Flight
            cursor.execute("""
                INSERT INTO Flights (flight_id, departure_date, airplane_id, source_airport, destination_airport, status, departure_time, runway_num)
                VALUES (%s, %s, %s, %s, %s, 'Active', %s, %s)
            """, (f_id, date, plane_id, source, dest, time, runway))

            # Insert Crew
            for pid in pilot_ids:
                cursor.execute(
                    "INSERT INTO Pilots_In_Flights (pilot_id, flight_id, departure_date) VALUES (%s, %s, %s)",
                    (pid, f_id, date))
            for aid in attendant_ids:
                cursor.execute(
                    "INSERT INTO Attendants_In_Flights (attendant_id, flight_id, departure_date) VALUES (%s, %s, %s)",
                    (aid, f_id, date))

            # Insert Prices
            cursor.execute("""
                INSERT INTO Classes_In_Flights (flight_id, departure_date, class_type, airplane_id, price)
                VALUES (%s, %s, 'Economy', %s, %s)
            """, (f_id, date, plane_id, price_economy))

            if price_business:
                cursor.execute("""
                    INSERT INTO Classes_In_Flights (flight_id, departure_date, class_type, airplane_id, price)
                    VALUES (%s, %s, 'Business', %s, %s)
                """, (f_id, date, plane_id, price_business))

            return True, "Flight Created Successfully!"
        except Exception as e:
            return False, str(e)

def get_filtered_resources(is_long_haul):
    """
    Fetches resources filtered by flight duration rules.
    NO JAVASCRIPT: The server decides what to show.
    """
    with db_cur() as cursor:
        # 1. Routes (Always needed for the top selector)
        cursor.execute("SELECT source_airport, destination_airport, flight_duration FROM Flight_Routes")
        routes = cursor.fetchall()

        # 2. Filter Planes
        # Rule: Long Haul -> Big Planes Only. Short Haul -> All Planes.
        if is_long_haul:
            cursor.execute("SELECT * FROM Airplanes WHERE size = 'Big'")
        else:
            cursor.execute("SELECT * FROM Airplanes")
        planes = cursor.fetchall()

        # 3. Filter Pilots
        # Rule: Long Haul -> Trained Pilots Only.
        if is_long_haul:
            cursor.execute("SELECT * FROM Pilots WHERE long_flight_training = 1")
        else:
            cursor.execute("SELECT * FROM Pilots")
        pilots = cursor.fetchall()

        # 4. Filter Attendants
        # Rule: Long Haul -> Trained Attendants Only.
        if is_long_haul:
            cursor.execute("SELECT * FROM Flight_Attendants WHERE long_flight_training = 1")
        else:
            cursor.execute("SELECT * FROM Flight_Attendants")
        attendants = cursor.fetchall()

    return routes, planes, pilots, attendants


# In code/utils.py

def create_new_route(source, dest, duration):
    """
    Adds a new flight route to the database if it doesn't exist.
    """
    # Basic validation
    if source.strip().upper() == dest.strip().upper():
        return False, "Source and Destination cannot be the same."

    if int(duration) <= 0:
        return False, "Flight duration must be positive."

    with db_cur() as cursor:
        try:
            # Check if route exists
            cursor.execute("""
                SELECT * FROM Flight_Routes 
                WHERE source_airport = %s AND destination_airport = %s
            """, (source, dest))

            if cursor.fetchone():
                return False, f"Route {source} -> {dest} already exists."

            # Insert new route
            cursor.execute("""
                INSERT INTO Flight_Routes (source_airport, destination_airport, flight_duration)
                VALUES (%s, %s, %s)
            """, (source, dest, duration))

            return True, f"Route {source} -> {dest} created successfully!"

        except Exception as e:
            return False, f"Database Error: {str(e)}"

def get_user_by_id(user_id):
    """
  Returns registered user or manager with given user id.
    """
    with db_cur() as cursor:
        cursor.execute("SELECT * FROM Registered_Customers WHERE email = %s", (user_id,))
        res = cursor.fetchone()
        
        if res:
            return RegisteredUser(
                email=res['email'],
                first_name=res['first_name'],
                middle_name=res['middle_name'],
                last_name=res['last_name'],
                passport_num=res['passport_num'],
                birth_date=res['birth_date'],
                password=res['password'],
                registration_date=res['registration_date']
            )
        cursor.execute("SELECT * FROM Managers WHERE manager_id = %s", (user_id,))
        res = cursor.fetchone()
        
        if res:
            return Manager(
                manager_id=res['manager_id'],
                first_name=res['first_name'],
                middle_name=res['middle_name'],
                last_name=res['last_name'],
                city=res['city'],
                street=res['street'],
                house_num=res['house_num'],
                start_date=res['start_date'],
                password=res['password']
            )
            
    return None


class FlightRoute:
    """
    Maps to Flight Routes table.
    """
    def __init__(self, source_airport, destination_airport, flight_duration):
        self.source_airport = source_airport
        self.destination_airport = destination_airport
        self.flight_duration = flight_duration


class Flight:
    """
    Maps to Flights table.
    """
    def __init__(self, flight_id, departure_date, airplane_id, source_airport, 
                 destination_airport, status, departure_time, runway_num):
        self.flight_id = flight_id
        self.departure_date = departure_date
        self.airplane_id = airplane_id
        self.source_airport = source_airport
        self.destination_airport = destination_airport
        self.status = status
        self.departure_time = departure_time
        self.runway_num = runway_num

    def get_datetime(self):
        """Helper to combine date and time for display"""
        return f"{self.departure_date} {self.departure_time}"


class Order:
    """
    Maps to Orders table.
    """
    def __init__(self, order_code, email, status, order_date, customer_type):
        self.order_code = order_code
        self.email = email
        self.status = status
        self.order_date = order_date
        self.customer_type = customer_type


class Ticket:
    """
    Maps to Flight Tickets table.
    """
    def __init__(self, order_code, flight_id, row_num, column_num, class_type, airplane_id, price):
        self.order_code = order_code
        self.flight_id = flight_id
        self.row_num = row_num
        self.column_num = column_num
        self.class_type = class_type
        self.airplane_id = airplane_id
        self.price = price

#returns a string of the seat number
    def get_seat_code(self):
        return f"{self.row_num}{self.column_num}"

def get_all_flights():
    """
   Retrieves all flights from database and returns as flight objects
    """
    flights_obj_list = []
    with db_cur() as cursor:
        cursor.execute("SELECT * FROM Flights")
        results = cursor.fetchall()
        
        for row in results:
            flight = Flight(
                flight_id=row['flight_id'],
                departure_date=row['departure_date'],
                airplane_id=row['airplane_id'],
                source_airport=row['source_airport'],
                destination_airport=row['destination_airport'],
                status=row['status'],
                departure_time=row['departure_time'],
                runway_num=row['runway_num']
            )
            flights_obj_list.append(flight)
            
    return flights_obj_list

def get_all_flight_routes(self):
    """
    Retrieves all flight routes from the database and returns as flight route objects
    """
    routes = []
    query = "SELECT source_airport, destination_airport, flight_duration FROM Flight_Routes"
    self.cursor.execute(query)
    
    for row in self.cursor.fetchall():
        route = {
            "source_airport": row[0],
            "destination_airport": row[1],
            "flight_duration": row[2]
        }
        routes.append(route)
        
    return routes

def get_all_orders(self):
    """
    Retrieves all orders from the database and returns as  order objects.
    """
    query = "SELECT order_code, email, status, order_date, customer_type FROM Orders"
    self.cursor.execute(query)

    orders = []
    for row in self.cursor.fetchall():
        new_order = Order(
            order_code=row[0],
            email=row[1],
            status=row[2],
            order_date=row[3],
            customer_type=row[4]
        )
        orders.append(new_order)

    return orders

def get_all_tickets(self):
    """
    Retrieves all flight tickets from the database and returns as ticket objects.
    """
    query = """
    SELECT order_code, flight_id, row_num, column_num, class_type, airplane_id, price 
    FROM Flight_Tickets
    """
    self.cursor.execute(query)

    tickets = []
    for row in self.cursor.fetchall():
        new_ticket = Ticket(
            order_code=row[0],
            flight_id=row[1],
            row_num=row[2],
            column_num=row[3],
            class_type=row[4],
            airplane_id=row[5],
            price=float(row[6]) if row[6] is not None else 0.0
        )
        tickets.append(new_ticket)

    return tickets

class Airplane:
    """
    Maps to Airplanes table.
    """
    def __init__(self, airplane_id, manufacturer, purchase_date, size):
        self.airplane_id = airplane_id
        self.manufacturer = manufacturer
        self.purchase_date = purchase_date
        self.size = size  # Enum: 'Small', 'Big'

    def __str__(self):
        return f"Airplane {self.airplane_id} ({self.manufacturer})"


class AirplaneClass:
    """
    Maps to Airplane Classes table.
    """
    def __init__(self, class_type, airplane_id, columns_count, rows_count):
        self.class_type = class_type
        self.airplane_id = airplane_id
        self.columns_count = columns_count
        self.rows_count = rows_count

    def __str__(self):
        return f"{self.class_type} class for Plane {self.airplane_id}"


class Seat:
    """
    Maps to Seats table.
    """
    def __init__(self, row_num, column_num, class_type, airplane_id):
        self.row_num = row_num
        self.column_num = column_num
        self.class_type = class_type
        self.airplane_id = airplane_id

    def __str__(self):
        return f"Seat {self.row_num}-{self.column_num} ({self.class_type})"

def get_all_airplanes(self):
    """
    Retrieves all airplanes from the database and returns as airplane object.
    """
    airplanes = []
    query = "SELECT airplane_id, manufacturer, purchase_date, size FROM Airplanes"
    self.cursor.execute(query)

    for row in self.cursor.fetchall():
        # CAUTION: Ensure you have an 'Airplane' class defined that accepts these arguments
        new_airplane = Airplane(
            airplane_id=row[0],
            manufacturer=row[1],
            purchase_date=row[2],
            size=row[3]
        )
        airplanes.append(new_airplane)

    return airplanes

def get_all_airplane_classes(self):
    """
    Retrieves all airplane class  from the database and returns as objects.
    """
    classes = []
    query = "SELECT class_type, airplane_id, columns_count, rows_count FROM Airplane_Classes"
    self.cursor.execute(query)

    for row in self.cursor.fetchall():
        new_class = AirplaneClass(
            class_type=row[0],
            airplane_id=row[1],
            columns_count=row[2],
            rows_count=row[3]
        )
        classes.append(new_class)

    return classes

def get_all_seats(self):
    """
    Retrieves all seats from the database.
    """
    seats = []
    query = "SELECT row_num, column_num, class_type, airplane_id FROM Seats"
    self.cursor.execute(query)

    for row in self.cursor.fetchall():
        # Check that your Seat class __init__ arguments match this order
        new_seat = Seat(
            row_num=row[0],
            column_num=row[1],
            class_type=row[2],
            airplane_id=row[3]
        )
        seats.append(new_seat)

    return seats

