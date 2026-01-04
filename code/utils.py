import random
import string
import datetime
from flask_login import UserMixin
import mysql.connector
from contextlib import contextmanager

# Configuration for your database connection
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "root", # Updated to your requested password
    "database": "FLYTAU",
    "autocommit": True
}
#Handles DB connection and cursor lifecycle
@contextmanager
def db_cur():
    mydb = None
    cursor = None
    try:
        mydb = mysql.connector.connect(**db_config)
        cursor = mydb.cursor(dictionary=True) # dictionary=True makes results easier to handle in Flask
        yield cursor
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        raise err
    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()

#User class for login
class User(UserMixin):
    def __init__(self, id, name, email, user_type):
        self.id = id  # This will be the email or ID if manager
        self.name = name
        self.email = email
        self.user_type = user_type  # 'Manager' or 'Registered'

# Enter an ID or email and receive the user
def get_user_by_id(user_id):
    """Load user for Flask-Login from either Customers or Managers tables."""
    with db_cur() as cursor:
        # Check Registered Customers
        cursor.execute("SELECT email, first_name FROM Registered_Customers WHERE email = %s", (user_id,))
        res = cursor.fetchone()
        if res:
            return User(id=res['email'], name=res['first_name'], email=res['email'], user_type='Registered')

        # Check managers if not found
        cursor.execute("SELECT manager_id, first_name FROM Managers WHERE manager_id = %s", (user_id,))
        res = cursor.fetchone()
        if res:
            return User(id=res['manager_id'], name=res['first_name'], email=None, user_type='Manager')
    return None

#Sign up logic
def register_new_customer(data):
    with db_cur() as cursor:
        try:
            # Check if user already exists
            cursor.execute("SELECT email FROM Registered_Customers WHERE email = %s", (data['email'],))
            if cursor.fetchone():
                return False, "Email already registered."

            # [cite_start]Insert into Registered_Customers
            # Registration date is set to current date automatically
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

            # [cite_start]Insert into Customer_Phones [cite: 13]
            insert_phone = "INSERT INTO Customer_Phones (phone_num, email, customer_type) VALUES (%s, %s, 'Registered')"
            cursor.execute(insert_phone, (data['phone'], data['email']))

            return True, "Account created successfully!"
        except Exception as e:
            print(f"Signup error: {e}")
            return False, "An error occurred during registration."

# Filters flights by user request
def get_flights_with_filters(user_type, date=None, source=None, destination=None):
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

#Returns a registered users order past present and future
def get_user_orders(email):
    with db_cur() as cursor:
        query = """
            SELECT o.order_code, o.status, o.order_date, 
                   SUM(t.price) as total_price, 
                   COUNT(t.flight_id) as ticket_count
            FROM Orders o
            JOIN Flight_Tickets t ON o.order_code = t.order_code
            WHERE o.email = %s
            GROUP BY o.order_code
        """
        cursor.execute(query, (email,))
        return cursor.fetchall()


#returns order by order id
def get_order_by_code(order_code, email):
    with db_cur() as cursor:
        # 1. Fetch overall order status and total price using SUM
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

        # 2. Fetch details for each individual ticket in this order
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

#cancel logic and excution
def cancel_order_logic(order_code):
    with db_cur() as cursor:
        # Get total price and flight time
        query = """
            SELECT f.departure_date, f.departure_time, SUM(t.price) as total_price
            FROM Flight_Tickets t
            JOIN Flights f ON t.flight_id = f.flight_id
            WHERE t.order_code = %s
            GROUP BY f.departure_date, f.departure_time
        """
        cursor.execute(query, (order_code,))
        res = cursor.fetchone()

        if not res: return "Order not found"

        # Check 36h rule
        flight_dt = datetime.combine(res['departure_date'], (datetime.min + res['departure_time']).time())
        if datetime.now() + timedelta(hours=36) > flight_dt:
            return "Cancellation only allowed up to 36 hours before flight"

        # Calculate 5% fee: $Fee = Total \times 0.05$
        cancellation_fee = float(res['total_price']) * 0.05

        # Update Order Status
        cursor.execute("UPDATE Orders SET status = 'Cancelled by customer' WHERE order_code = %s", (order_code,))

        # Update price to reflect only the fee paid
        cursor.execute(
            "UPDATE Flight_Tickets SET price = %s / (SELECT COUNT(*) FROM Flight_Tickets WHERE order_code = %s) WHERE order_code = %s",
            (cancellation_fee, order_code, order_code))
        return True

#Returns flight details using flight ID
def get_flight_details(flight_id):
    with db_cur() as cursor:
        query = "SELECT * FROM Flights WHERE flight_id = %s"
        cursor.execute(query, (flight_id,))
        return cursor.fetchone()

#Returns all seats for flight and if occupied or not
def get_seats_for_flight(flight_id):
    with db_cur() as cursor:
        # Get the airplane_id for this flight
        cursor.execute("SELECT airplane_id FROM Flights WHERE flight_id = %s", (flight_id,))
        flight = cursor.fetchone()
        if not flight: return []

        # Join Seats with Flight_Tickets to check occupancy
        # If a ticket exists for this seat/flight combo, is_taken is 1 (True)
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

#    Returns the flight details and seat list
    #Create a seat map and checks which seats are occupied in flight  tickets
def get_flight_seat_map(flight_id):
    with db_cur() as cursor:
        # Extract the flight details and airplanes to know the number of seats
        query_flight = """
            SELECT f.*, a.size 
            FROM Flights f 
            JOIN Airplanes a ON f.airplane_id = a.airplane_id 
            WHERE f.flight_id = %s
        """
        cursor.execute(query_flight, (flight_id,))
        flight = cursor.fetchone()

        if not flight:
            return None, []

        # 2.Decide the number of rows and number of classes each airplain has. Big airplane - 2 classes, 40 rows. Small airplane - 1 class, 20 rows
        rows = 40 if flight['size'] == 'Big' else 20
        cols = ['A', 'B', 'C', 'D', 'E', 'F']

        # 3. Checks for occupied seats
        cursor.execute("SELECT row_num, column_num FROM Flight_Tickets WHERE flight_id = %s", (flight_id,))
        taken_seats = {(r['row_num'], r['column_num']) for r in cursor.fetchall()}

        # 4. Builds the list of seats in HTML
        seats_list = []
        for r in range(1, rows + 1):
            for c in cols:
                is_taken = (r, c) in taken_seats
                seats_list.append({
                    'row_num': r,
                    'column_num': c,
                    'is_taken': is_taken
                })

        return flight, seats_list
# check the dictionary logic
# Global dictionary to store manager-defined prices. Structure: {'flight_id': {'Economy': price, 'Business': price}}
MANAGER_PRICES = {}

#Return current price for ticket, if none gives 350 fo buiseness and 150 for economy
def get_current_price(flight_id, class_type):
    """Retrieves the price set by manager or uses fallback values."""
    if flight_id in MANAGER_PRICES and class_type in MANAGER_PRICES[flight_id]:
        return MANAGER_PRICES[flight_id][class_type]
    
    # Fallback as requested: 150 for Economy, 350 for Business
    return 350.00 if class_type == 'Business' else 150.00


'''
Need to think if the function below (create_booking is needed) is needed
'''
def create_booking(flight_id, selected_seats, user, guest_data=None):
    """
    Creates a booking, handles guest registration, and assigns dynamic pricing.
    """
    with db_cur() as cursor:
        try:
            # Generate unique 8-character Order Code 
            order_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            # 2. Handle Customer Identification
            if user.is_authenticated:
                email = user.id
                customer_type = 'Registered'
            else:
                email = guest_data['email']
                customer_type = 'Unregistered'
                # Check if guest exists; if not, add them
                cursor.execute("SELECT email FROM Unregistered_Customers WHERE email = %s", (email,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO Unregistered_Customers (email, first_name, middle_name, last_name, customer_type)
                        VALUES (%s, %s, %s, %s, 'Unregistered')
                    """, (email, guest_data['first_name'], guest_data.get('middle_name'), 
                          guest_data['last_name']))

            # Create the Order
            cursor.execute("""
                INSERT INTO Orders (order_code, email, status, order_date, customer_type)
                VALUES (%s, %s, 'Active', CURDATE(), %s)
            """, (order_code, email, customer_type))

            # Insert Tickets with Dynamic Pricing 
            for seat_key in selected_seats:
                # seat_key format: "row-col-airplane_id"
                row, col, airplane_id = seat_key.split('-')
                
                # Fetch seat class (Economy/Business)
                cursor.execute("""
                    SELECT class_type FROM Seats 
                    WHERE row_num = %s AND column_num = %s AND airplane_id = %s
                """, (row, col, airplane_id))
                seat_info = cursor.fetchone()
                class_type = seat_info['class_type']

                # Fetch dynamic price set by manager for this flight/class by inserting individual tickets to the order
                for seat_key in selected_seats:
                # Expecting seat_key format: "row-col-class-airplane_id"
                    row, col, s_class, airplane_id = seat_key.split('-')
                
                cursor.execute("""
                    SELECT price FROM Flight_Pricing 
                    WHERE flight_id = %s AND class_type = %s
                    LIMIT 1
                """, (flight_id, class_type))
                price_res = cursor.fetchone()
                if price_res:
                    ticket_price = price_res['price']
                else:
                    ticket_price = 350.00 if s_class == 'Business' else 150.00 #Fallback

                cursor.execute("""
                    INSERT INTO Flight_Tickets (order_code, flight_id, row_num, column_num, class_type, airplane_id, price)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (order_code, flight_id, row, col, class_type, airplane_id, ticket_price))

            return True, "Booking successful!", order_code
        except Exception as e:
            print(f"Booking Error: {e}")
            return False, "Failed to complete booking. Please try again.", None

#Creates father class worker for all types of employees
class Worker:
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

#Create pilot class with function to return type
class Pilot(Worker):
    def __init__(self, pilot_id, first_name, middle_name, last_name, city, street, house_num, start_date, long_flight_training):
        super().__init__(first_name, middle_name, last_name, city, street, house_num, start_date)
        self.id = pilot_id
        # In SQL this is BOOLEAN/TINYINT (0 or 1)
        self.long_flight_training = True if long_flight_training else False

    def get_role(self):
        return "Pilot"

#Create flight attendant class with function to return type
class FlightAttendant(Worker):
    def __init__(self, attendant_id, first_name, middle_name, last_name, city, street, house_num, start_date, long_flight_training):
        super().__init__(first_name, middle_name, last_name, city, street, house_num, start_date)
        self.id = attendant_id
        self.long_flight_training = True if long_flight_training else False

    def get_role(self):
        return "Flight Attendant"

#Create manager class with function to return type
class Manager(Worker):
    def __init__(self, manager_id, first_name, middle_name, last_name, city, street, house_num, start_date):
        super().__init__(first_name, middle_name, last_name, city, street, house_num, start_date)
        self.id = manager_id

    def get_role(self):
        return "Manager"

#  Fetches rows from Pilots table and converts them to Pilot objects.
def get_all_pilots():
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

#  Fetches rows from flight attendants table and converts them to Pilot objects.
def get_all_attendants():
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

#  Fetches rows from managers table and converts them to Pilot objects.
def get_all_managers(manager_id):
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


class User(UserMixin):
    """
    מחלקת בסיס המייצגת משתמש כללי במערכת.
    מכילה את השדות המשותפים לכולם: אימייל, שם פרטי, שם אמצעי ושם משפחה.
    משמשת גם עבור אורחים (Guests) וגם כבסיס למשתמשים רשומים.
    """
    def __init__(self, email, first_name, last_name, middle_name=None):
        self.id = email  
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.middle_name = middle_name
        self.user_type = 'Guest' 

    def get_full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

# Class that represents registered users
class RegisteredUser(User):
    def __init__(self, email, first_name, last_name, passport_num, birth_date, password, registration_date, middle_name=None):
        super().__init__(email, first_name, last_name, middle_name)        
        self.passport_num = passport_num
        self.birth_date = birth_date
        self.password = password
        self.registration_date = registration_date
        self.user_type = 'Registered' 

def get_user_by_id(user_id):
    """
    פונקציה שטוענת משתמש (רשום או מנהל) עבור Flask-Login.
    """
    with db_cur() as cursor:
        # 1. בדיקה אם המשתמש הוא לקוח רשום
        # שימו לב: אנחנו שולפים את כל הפרטים כדי ליצור אובייקט RegisteredUser מלא
        cursor.execute("SELECT * FROM Registered_Customers WHERE email = %s", (user_id,))
        res = cursor.fetchone()
        
        if res:
            # יצירת אובייקט מהמחלקה החדשה שבנינו
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

        # 2. בדיקה אם המשתמש הוא מנהל (משתמשים במחלקה שיצרנו קודם)
        # שימו לב: הנחת העבודה היא שהוספתם עמודת password למנהלים כפי שסוכם
        cursor.execute("SELECT * FROM Managers WHERE manager_id = %s", (user_id,))
        res = cursor.fetchone()
        
        if res:
            # שימוש במחלקת Manager שיצרנו בשלבים הקודמים
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

#Class that maps to flight route table
class FlightRoute:
    def __init__(self, source_airport, destination_airport, flight_duration):
        self.source_airport = source_airport
        self.destination_airport = destination_airport
        self.flight_duration = flight_duration  # In minutes

##Class that maps to flight table
class Flight:
    def __init__(self, flight_id, departure_date, airplane_id, source_airport, 
                 destination_airport, status, departure_time, runway_num):
        self.flight_id = flight_id
        self.departure_date = departure_date
        self.airplane_id = airplane_id
        self.source_airport = source_airport
        self.destination_airport = destination_airport
        self.status = status  # Enum: Active, Full Capacity, Arrived, Cancelled
        self.departure_time = departure_time
        self.runway_num = runway_num

    def get_datetime(self):
        """Helper to combine date and time for display"""
        return f"{self.departure_date} {self.departure_time}"

#Class that maps to orders table
class Order:
    def __init__(self, order_code, email, status, order_date, customer_type):
        self.order_code = order_code
        self.email = email
        self.status = status  # Enum: Active, Executed, Cancelled by...
        self.order_date = order_date
        self.customer_type = customer_type  # 'Registered' or 'Unregistered'

#Class that maps to ticket table
class Ticket:
    def __init__(self, order_code, flight_id, row_num, column_num, class_type, airplane_id, price):
        self.order_code = order_code
        self.flight_id = flight_id
        self.row_num = row_num
        self.column_num = column_num
        self.class_type = class_type  # 'Economy' or 'Business'
        self.airplane_id = airplane_id
        self.price = price

    def get_seat_code(self):
        return f"{self.row_num}{self.column_num}"

#Returns all flights as flight object
def get_all_flights():
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

#returns all flight routes from DB
def get_all_flight_routes(self):
    routes = []
    # Explicitly selecting columns ensures the mapping below is always correct
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

#returns all orders from DB
def get_all_orders(self):
    orders = []
    query = "SELECT order_code, email, status, order_date, customer_type FROM Orders"
    self.cursor.execute(query)
    
    for row in self.cursor.fetchall():
        order = {
            "order_code": row[0],
            "email": row[1],
            "status": row[2],       # This will be 'Active', 'Executed', etc.
            "order_date": row[3],
            "customer_type": row[4] # 'Registered' or 'Unregistered'
        }
        orders.append(order)
        
    return orders

#returns all tickets from DB
def get_all_tickets(self):
    """
    Retrieves all flight tickets from the database.
    """
    tickets = []
    query = """
    SELECT order_code, flight_id, row_num, column_num, class_type, airplane_id, price 
    FROM Flight_Tickets
    """
    self.cursor.execute(query)
    
    for row in self.cursor.fetchall():
        ticket = {
            "order_code": row[0],
            "flight_id": row[1],
            "row_num": row[2],
            "column_num": row[3],
            "class_type": row[4],  # 'Economy' or 'Business'
            "airplane_id": row[5],
            "price": float(row[6]) if row[6] is not None else 0.0 # Convert Decimal to float for Python handling
        }
        tickets.append(ticket)
        
    return tickets

#Class that maps to airplane in SQL
class Airplane:
    def __init__(self, airplane_id, manufacturer, purchase_date, size):
        self.airplane_id = airplane_id
        self.manufacturer = manufacturer
        self.purchase_date = purchase_date
        self.size = size  # Enum: 'Small', 'Big'

    def __str__(self):
        return f"Airplane {self.airplane_id} ({self.manufacturer})"

#Class that maps to airplane class in SQL
class AirplaneClass:
    def __init__(self, class_type, airplane_id, columns_count, rows_count):
        self.class_type = class_type  # Enum: 'Economy', 'Business'
        self.airplane_id = airplane_id
        self.columns_count = columns_count
        self.rows_count = rows_count

    def __str__(self):
        return f"{self.class_type} class for Plane {self.airplane_id}"

#Maps to Seat in SQL
class Seat:
    def __init__(self, row_num, column_num, class_type, airplane_id):
        self.row_num = row_num
        self.column_num = column_num
        self.class_type = class_type
        self.airplane_id = airplane_id

    def __str__(self):
        return f"Seat {self.row_num}-{self.column_num} ({self.class_type})"

#Returns all airplanes from DB
def get_all_airplanes(self):
    airplanes = []
    # Explicitly selecting columns to match the dictionary below
    query = "SELECT airplane_id, manufacturer, purchase_date, size FROM Airplanes"
    self.cursor.execute(query)
    
    for row in self.cursor.fetchall():
        airplane = {
            "airplane_id": row[0],
            "manufacturer": row[1],
            "purchase_date": row[2],
            "size": row[3]  # 'Small' or 'Big'
        }
        airplanes.append(airplane)
        
    return airplanes

#Returns all airplanes classes from DB
def get_all_airplane_classes(self):
    classes = []
    query = "SELECT class_type, airplane_id, columns_count, rows_count FROM Airplane_Classes"
    self.cursor.execute(query)
    
    for row in self.cursor.fetchall():
        a_class = {
            "class_type": row[0],     # 'Economy' or 'Business'
            "airplane_id": row[1],
            "columns_count": row[2],
            "rows_count": row[3]
        }
        classes.append(a_class)
        
    return classes

#Returns all seats from DB
def get_all_seats(self):
    seats = []
    query = "SELECT row_num, column_num, class_type, airplane_id FROM Seats"
    self.cursor.execute(query)
    
    for row in self.cursor.fetchall():
        seat = {
            "row_num": row[0],
            "column_num": row[1],
            "class_type": row[2],   # 'Economy' or 'Business'
            "airplane_id": row[3]
        }
        seats.append(seat)
        
    return seats
