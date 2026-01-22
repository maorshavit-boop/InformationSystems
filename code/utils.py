import random
import string
from flask_login import UserMixin
import mysql.connector
from contextlib import contextmanager

# Configuration for database connection
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "FLYTAU",
    "autocommit": True
}


# Context manager to handle database connection and cursor lifecycle.
@contextmanager
def db_cur():
    """
    Context manager that establishes a database connection and yields a
    dictionary cursor for executing SQL queries.
    Yields: MySQLCursorDict: A cursor object that returns query results as dictionaries.
    Raises: mysql.connector.Error: If a database connection error occurs.
    """
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
    Backend logic for registering a new customer.
    Inserts customer details into 'Registered_Customers' and associated phone numbers
    into 'Customer_Phones'.
    parm data (dict): A dictionary containing user registration details (email, names, passport, etc.).
    Returns: tuple: (bool, str) - (True, "Success Message") or (False, "Error Message").
    """
    with db_cur() as cursor:
        try:
            # Check if email exists in Registered Customers
            cursor.execute("SELECT email FROM Registered_Customers WHERE email = %s", (data['email'],))
            if cursor.fetchone():
                return False, "Email already registered."

            # [NEW] SECURITY CHECK: Check if email exists in Managers
            cursor.execute("SELECT manager_id FROM Managers WHERE email = %s", (data['email'],))
            if cursor.fetchone():
                return False, "Managers are not allowed to register as customers."

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
            phone_list = data.get('phones', [])
            if isinstance(phone_list, str):
                phone_list = [phone_list]

            for phone in phone_list:
                if phone and phone.strip():
                    cursor.execute(insert_phone, (phone.strip(), data['email']))

            return True, "Account created successfully!"

        except Exception as e:
            print(f"Signup error: {e}")
            return False, "An error occurred during registration."


def get_flights_with_filters(user_type, date=None, source=None, destination=None, status=None):
    """
    Retrieves a list of flights based on the user type and optional filters.
    Managers see all flights; others see only 'Active' flights.
    param: user_type (str): The type of user requesting the data ('Manager' or other).
    param date (str, optional): Filter by departure date (YYYY-MM-DD).
    param source (str, optional): Filter by source airport code.
    param destination (str, optional): Filter by destination airport code.
    Returns: list[dict]: A list of flight records matching the criteria.
    """

    with db_cur() as cursor:
        params = []

        if user_type == 'Manager':
            query = "SELECT * FROM Flights WHERE 1=1"

            if status and status != 'All':
                query += " AND status = %s"
                params.append(status)

        else:
            query = "SELECT * FROM Flights WHERE status = 'Active'"

        if date:
            query += " AND departure_date = %s"
            params.append(date)
        if source:
            query += " AND source_airport = %s"
            params.append(source)
        if destination:
            query += " AND destination_airport = %s"
            params.append(destination)

        cursor.execute(query, tuple(params))
        return cursor.fetchall()


from datetime import datetime, timedelta


def get_customer_history(email, status_filter=None):
    """
    Retrieves the order history for a specific customer, optionally filtered by status.
    Aggregates ticket count and total price per order.
    param email (str): The email address of the customer.
    param status_filter (str, optional): Status to filter by ('All', 'Cancelled', etc.).
    Returns: list[dict]: A list of orders with aggregated details.
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
                   COALESCE(SUM(FT.price),0) as total_price, 
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
    Fetches detailed information for a specific order, including general info and specific tickets.
    param order_code (str): The unique code of the order.
    param email (str): The email of the customer who owns the order.
    Returns: dict: A dictionary with keys 'info' (order summary) and 'tickets' (list of tickets),
              or None if the order is not found.
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
    Executes an order cancellation process.
    Validates the cancellation window (up to 36 hours before flight), calculates a 5% fee,
    updates the order status, and adjusts ticket prices to reflect the fee.
    param order_code (str): The code of the order to cancel.
    Returns: tuple: (bool, str) - (True, "Success Message") or (False, "Error Message").
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
    """
    Retrieves basic details for a specific flight by its ID.
    param flight_id (str): The unique identifier of the flight.
    Returns: dict: A dictionary containing flight details, or None if not found.
    """

    with db_cur() as cursor:
        query = "SELECT * FROM Flights WHERE flight_id = %s"
        cursor.execute(query, (flight_id,))
        return cursor.fetchone()


def get_flight_seat_map(flight_id):
    """
    Generates a seat map for a flight, indicating occupied seats.
    Returns the raw flight info and a structured map for frontend rendering.
    param flight_id (str): The unique identifier of the flight.
    Returns: tuple: (dict, dict) - Flight details and a seat map dictionary {row: {col: seat_data}}.
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


def get_current_price(flight_id, class_type):
    """
    Retrieves the current ticket price for a specific flight and class type.
    param flight_id (str): The flight identifier.
    param class_type (str): The class (e.g., 'Economy', 'Business').
    Returns: float: The price of the ticket.
    Raises: ValueError: If no price is found for the specified class and flight.
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
        raise ValueError(
            f"CRITICAL: No price set for Flight {flight_id} in {class_type} class. Please choose a different ticket")


# Creates a booking
def create_booking(flight_id, selected_seats, user, guest_data=None):
    """
    Handles the creation of a new flight booking.
    Manages user type (Registered/Guest), creates an order, and inserts tickets.
    param flight_id (str): The flight ID being booked.
    param selected_seats (list): List of seat strings ("row-col-class-planeID").
    param user (UserMixin): The currently logged-in user object.
    param guest_data (dict, optional): Details for a guest user if not logged in.
    Returns: tuple: (bool, str, str) - (Success, Message, OrderCode).
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
                if getattr(user, 'user_type', '') == 'Manager':
                    return False, "Managers cannot book flights!", None
                email = user.id
                customer_type = 'Registered'
            else:
                email = guest_data['email']
                # security check: Is this email a Manager's email?
                cursor.execute("SELECT manager_id FROM Managers WHERE email = %s", (email,))
                if cursor.fetchone():
                    return False, "Corruption Alert: Managers are forbidden from booking tickets (even as guests).", None
                customer_type = 'Unregistered'

                # Check if guest exists, if not create them
                cursor.execute("SELECT email FROM Unregistered_Customers WHERE email = %s", (email,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO Unregistered_Customers (email, first_name, middle_name, last_name, customer_type)
                        VALUES (%s, %s, %s, %s, 'Unregistered')
                    """, (email, guest_data['first_name'], guest_data.get('middle_name'), guest_data['last_name']))

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
                current_price = price_check['price']

                # Insert Ticket
                cursor.execute("""
                    INSERT INTO Flight_Tickets 
                    (order_code, flight_id, departure_date, row_num, column_num, class_type, airplane_id, price)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (order_code, flight_id, departure_date, row, col, s_class, airplane_id, current_price))

            return True, "Booking successful!", order_code
        except Exception as e:
            print(f"Booking Error: {e}")
            return False, str(e), None


class Worker:
    """
    Base class representing a general employee/worker in the system.
    Stores common attributes like name and address.
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
        """Returns the worker's full name, including middle name if present."""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    def get_address(self):
        """Returns the formatted address string."""
        return f"{self.street} {self.house_num}, {self.city}"


class Manager(Worker, UserMixin):
    """
    Represents a Manager user, inheriting from Worker and UserMixin for Flask-Login compatibility.
    Includes login credentials (manager_id, password).
    """

    def __init__(self, manager_id, password, first_name, middle_name, last_name, city, street, house_num, start_date):
        super().__init__(first_name, middle_name, last_name, city, street, house_num, start_date)
        self.id = manager_id
        self.password = password
        self.user_type = 'Manager'

    def get_role(self):
        """Returns the user role string."""
        return "Manager"


class User(UserMixin):
    """
    Base class representing a generic user (e.g., Guest/Unregistered).
    """

    def __init__(self, email, first_name, last_name, middle_name=None):
        self.id = email
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.middle_name = middle_name
        self.user_type = 'Guest'

    def get_full_name(self):
        """Returns the user's full name."""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"


class RegisteredUser(User):
    """
    Represents a registered customer with extended details like passport and password.
    Inherits from User.
    """

    def __init__(self, email, first_name, last_name, passport_num, birth_date, password, registration_date,
                 middle_name=None):
        super().__init__(email, first_name, last_name, middle_name)
        self.passport_num = passport_num
        self.birth_date = birth_date
        self.password = password
        self.registration_date = registration_date
        self.user_type = 'Registered'


# Helper to check Runway Availability (15 min buffer)
def check_runway_conflict(date, time, runway):
    """
    Validates if a runway is free for a given time window (15-minute buffer).
    param date (str): Departure date.
    param time (str): Departure time.
    param runway (str): Runway number.
    Returns: str: Conflict message if collision exists, else None.
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
    Fetches available planes, pilots, and attendants that do not have conflicting schedules
    for the specified time window. Also handles logic for 'Long Haul' requirements.
    param date (str): Flight date.
    param new_start_time (str): Flight start time.
    param new_duration (int): Flight duration in minutes.
    Returns: tuple: (planes, pilots, attendants) - Lists of available resource records.
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


def check_plane_availability(plane_id, date, new_start_time, new_duration):
    """
    Checks if a specific plane is available during the requested time window,
    considering the duration of both the new flight and existing flights.
    param plane_id (str): The ID of the aircraft.
    param date (str): Flight date.
    param new_start_time (str): Flight start time.
    param new_duration (int): Flight duration.
    Returns: str: Conflict message if busy, else None.
    """

    with db_cur() as cursor:
        cursor.execute("""
            SELECT f.flight_id, f.departure_time, r.flight_duration
            FROM Flights f
            JOIN Flight_Routes r ON f.source_airport = r.source_airport AND f.destination_airport = r.destination_airport
            WHERE f.departure_date = %s
              AND f.airplane_id = %s
              AND f.status != 'Cancelled'
              AND (
                  -- 1. Existing flight starts inside new flight's window
                  f.departure_time < ADDTIME(%s, SEC_TO_TIME((%s + 60)*60))
                  AND 
                  -- 2. New flight starts inside existing flight's window
                  %s < ADDTIME(f.departure_time, SEC_TO_TIME((r.flight_duration + 60)*60))
              )
        """, (date, plane_id, new_start_time, new_duration, new_start_time))

        conflict = cursor.fetchone()
        if conflict:
            return f"Aircraft Conflict: Plane {plane_id} is busy with Flight {conflict['flight_id']}."
    return None


def check_flight_id_exists(flight_id):
    """
    Checks if a flight ID already exists in the database.
    param flight_id (str): The flight ID to check.
    Returns: bool: True if exists, False otherwise.
    """

    with db_cur() as cursor:
        cursor.execute("SELECT flight_id FROM Flights WHERE flight_id = %s", (flight_id,))
        if cursor.fetchone():
            return True
    return False


def create_flight_final_step(form_data):
    """
    Performs the final validation and insertion of a new flight.
    Validates resources (plane, runway, crew training) and inserts data into multiple tables.
    param form_data (dict): Dictionary containing form inputs for the new flight.
    Returns: tuple: (bool, str) - (Success, Message).
    """

    f_id = form_data['flight_id']
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

    # We fetch it from DB to ensure accuracy
    with db_cur() as cursor:
        cursor.execute("SELECT flight_duration FROM Flight_Routes WHERE source_airport=%s AND destination_airport=%s",
                       (source, dest))
        route_res = cursor.fetchone()
        if not route_res:
            return False, "Error: Route not found."
        duration = route_res['flight_duration']

        cursor.execute("SELECT size FROM Airplanes WHERE airplane_id=%s", (plane_id,))
        p_res = cursor.fetchone()
        if not p_res: return False, "Plane not found."
        plane_size = p_res['size']


    if plane_size == 'Big':
        req_pilots = 3
        req_attendants = 6
    else:
        req_pilots = 2
        req_attendants = 3

    if len(pilot_ids) != req_pilots:
        return False, f"Crew mismatch: {plane_size} plane requires {req_pilots} Pilots (you selected {len(pilot_ids)})."
    if len(attendant_ids) != req_attendants:
        return False, f"Crew mismatch: {plane_size} plane requires {req_attendants} Attendants (you selected {len(attendant_ids)})."

    # 2. RUN FINAL SAFETY CHECKS (Race Conditions)
    if check_flight_id_exists(f_id):
        return False, f"CRITICAL: Flight ID {f_id} was taken by another manager just now."

    if check_runway_conflict(date, time, runway):
        return False, "CRITICAL: Runway conflict detected (Race Condition)."

    plane_conflict = check_plane_availability(plane_id, date, time, duration)
    if plane_conflict:
        return False, f"CRITICAL: {plane_conflict}"

    # 3. INSERT DATA
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

def create_new_route(source, dest, duration):
    """
    Inserts a new flight route into the 'Flight_Routes' table if it doesn't already exist.
    param source (str): Source airport code.
    param dest (str): Destination airport code.
    param duration (int): Flight duration in minutes.
    Returns: tuple: (bool, str) - (Success, Message).
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
    Factory function to retrieve a user object (RegisteredUser or Manager) by ID.
    Used by Flask-Login for user loading.
    param user_id (str): The unique ID of the user (email for customers, manager_id for managers).
    Returns: UserMixin: An instance of RegisteredUser or Manager, or None if not found.
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


def add_new_worker(data):
    """
    Adds a new worker (Pilot or Flight Attendant) to the database.
    Generates a new unique ID and inserts the worker's details.
    param data (dict): Dictionary containing worker details (role, names, address, training).
    Returns: tuple: (bool, str) - (Success, Message).
    """

    role = data.get('role')  # 'Pilot' or 'Attendant'

    # ID Generation
    prefix = "P" if role == 'Pilot' else "FA"
    table = "Pilots" if role == 'Pilot' else "Flight_Attendants"
    col_id = "pilot_id" if role == 'Pilot' else "attendant_id"

    # Data extraction
    first = data.get('first_name')
    last = data.get('last_name')
    middle = data.get('middle_name')
    city = data.get('city')
    street = data.get('street')
    house = data.get('house_num')

    # Handle Checkbox (returns 'on' if checked, None if not)
    is_trained = 1 if data.get('long_flight_training') else 0

    with db_cur() as cursor:
        # Find next ID
        cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
        count = cursor.fetchone()['cnt'] + 1
        new_id = f"{prefix}-{str(count).zfill(3)}"

        try:
            query = f"""
                INSERT INTO {table} 
                ({col_id}, first_name, middle_name, last_name, city, street, house_num, start_date, long_flight_training) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURDATE(), %s)
            """
            cursor.execute(query, (new_id, first, middle, last, city, street, house, is_trained))
            return True, f"Added {role} {new_id} successfully."
        except Exception as e:
            return False, str(e)
