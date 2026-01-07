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


def seed_seats():
    with db_cur() as cursor:
        cursor.execute("SELECT airplane_id, size FROM Airplanes")
        airplanes = cursor.fetchall()

        for plane in airplanes:
            current_row_start = 1

            if plane['size'] == 'Big':
                classes = [('Business', 4, 6), ('Economy', 25, 6)]
            else:
                classes = [('Economy', 20, 6)]

            for class_type, rows_count, cols_count in classes:
                cursor.execute("""
                    INSERT IGNORE INTO Airplane_Classes (class_type, airplane_id, rows_count, columns_count)
                    VALUES (%s, %s, %s, %s)
                """, (class_type, plane['airplane_id'], rows_count, cols_count))
                for r in range(current_row_start, current_row_start + rows_count):
                    for c in range(1, cols_count + 1):
                        cursor.execute("""
                            INSERT IGNORE INTO Seats (row_num, column_num, class_type, airplane_id)
                            VALUES (%s, %s, %s, %s)
                        """, (r, c, class_type, plane['airplane_id']))
                current_row_start += rows_count


def seed_full_database():
    with db_cur() as cursor:
        airplanes = [
            ('AP-BIG-1', 'Boeing', '2018-05-01', 'Big'),
            ('AP-SML-1', 'Airbus', '2019-08-20', 'Small')
        ]
        cursor.executemany("INSERT IGNORE INTO Airplanes VALUES (%s, %s, %s, %s)", airplanes)

        # 2. יצירת מנהלים - סדר העמודות: id, password, first, middle, last, city, street, house, date
        managers = [
            ('M001', 'pass123', 'Boss', 'The', 'Manager', 'Tel Aviv', 'Azrieli', '1', '2010-01-01'),
            ('M002', 'admin456', 'Big', 'Chief', 'Officer', 'Herzliya', 'Pituach', '2', '2012-02-02')
        ]
        # שים לב שיש כאן 9 סימני %s שמתאימים ל-9 ערכים ול-9 עמודות בטבלה המעודכנת
        cursor.executemany("INSERT IGNORE INTO Managers VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", managers)

        # 3. יצירת טיסות (לפחות 4 כפי שנדרש בעמ' 5)
        flights = [
            ('FL101', '2026-06-01', 'AP-BIG-1', 'TLV', 'JFK', 'Active', '08:00:00', 'R1'),
            ('FL102', '2026-06-02', 'AP-BIG-1', 'JFK', 'TLV', 'Active', '20:00:00', 'R4L'),
            ('FL103', '2026-06-01', 'AP-SML-1', 'TLV', 'ETM', 'Active', '07:00:00', 'R2'),
            ('FL104', '2026-06-15', 'AP-BIG-1', 'TLV', 'LHR', 'Active', '10:00:00', 'R1')
        ]
        cursor.executemany("INSERT IGNORE INTO Flights VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", flights)

        # הרצת יצירת המושבים עבור המטוסים החדשים
        seed_seats()
        cursor.commit()


def register_new_customer(data):
    """
    Backend logic for user signup.
    Inserts data into Registered_Customers and Customer_Phones.
    """
    with db_cur() as cursor:
        try:
            cursor.execute("SELECT email FROM Registered_Customers WHERE email = %s", (data['email'],))
            if cursor.fetchone():
                return False, "Email already registered."
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
            insert_phone = "INSERT INTO Customer_Phones (phone_num, email, customer_type) VALUES (%s, %s, 'Registered')"
            cursor.execute(insert_phone, (data['phone'], data['email']))
            cursor.commit()
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


def get_customer_history(email):
    """
    Returns all orders for a specific user, including flight details (destination, date)
    and total price.
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
            WHERE O.email = %s
            GROUP BY O.order_code, O.status, O.order_date, F.flight_id, 
                     F.source_airport, F.destination_airport, F.departure_date, F.departure_time
            ORDER BY O.order_date DESC
        """
        cursor.execute(query, (email,))
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
            WHERE o.order_code = %s AND o.email = %s
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
    """Returns flight details and seat map"""
    with db_cur() as cursor:
        query_flight = """
            SELECT f.*, a.size, a.airplane_id 
            FROM Flights f 
            JOIN Airplanes a ON f.airplane_id = a.airplane_id 
            WHERE f.flight_id = %s
        """
        cursor.execute(query_flight, (flight_id,))
        flight = cursor.fetchone()

        if not flight:
            return None, []
        query_seats = """
            SELECT s.row_num, s.column_num, s.class_type,
                   CASE WHEN t.order_code IS NOT NULL THEN 1 ELSE 0 END AS is_taken
            FROM Seats s
            LEFT JOIN Flight_Tickets t 
                ON s.row_num = t.row_num 
                AND s.column_num = t.column_num 
                AND s.airplane_id = t.airplane_id
                AND t.flight_id = %s
            WHERE s.airplane_id = %s
            ORDER BY s.row_num, s.column_num
        """
        cursor.execute(query_seats, (flight_id, flight['airplane_id']))
        seats_list = cursor.fetchall()

        return flight, seats_list

MANAGER_PRICES = {}

#NEED TO CHECK ABOUT FALLBACK VALUES!!
def get_current_price(flight_id, class_type):
    """Retrieves the price set by manager or uses fallback values."""
    if flight_id in MANAGER_PRICES and class_type in MANAGER_PRICES[flight_id]:
        return MANAGER_PRICES[flight_id][class_type]
    return 350.00 if class_type == 'Business' else 150.00


#Creates a booking
def create_booking(flight_id, selected_seats, user, guest_data=None):
    with db_cur() as cursor:
        try:
            order_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if user.is_authenticated:
                email = user.id
                customer_type = 'Registered'
            else:
                email = guest_data['email']
                customer_type = 'Unregistered'
                cursor.execute(
                    "INSERT IGNORE INTO Unregistered_Customers (email, first_name, last_name, customer_type) VALUES (%s, %s, %s, %s)",
                    (email, guest_data['first_name'], guest_data['last_name'], customer_type))
            cursor.execute("""
                INSERT INTO Orders (order_code, email, status, order_date, customer_type)
                VALUES (%s, %s, 'Active', CURDATE(), %s)
            """, (order_code, email, customer_type))
            for seat_key in selected_seats:
                row, col, s_class, airplane_id = seat_key.split('-')

                # NEED TO CHECK THE FALLBACK VALUES
                price = 350.00 if s_class == 'Business' else 150.00
                cursor.execute("""
                    INSERT INTO Flight_Tickets (order_code, flight_id, row_num, column_num, class_type, airplane_id, price)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (order_code, flight_id, row, col, s_class, airplane_id, price))
            cursor.commit()
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
