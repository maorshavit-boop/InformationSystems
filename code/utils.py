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

@contextmanager
def db_cur():
    """Context manager to handle database connection and cursor lifecycle."""
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


class User(UserMixin):
    """User class for Flask-Login[cite: 79]."""

    def __init__(self, id, name, email, user_type):
        self.id = id  # This will be the email or ID
        self.name = name
        self.email = email
        self.user_type = user_type  # 'Manager' or 'Registered'


def get_user_by_id(user_id):
    """Load user for Flask-Login from either Customers or Managers tables."""
    with db_cur() as cursor:
        # Check Registered Customers
        cursor.execute("SELECT email, first_name FROM Registered_Customers WHERE email = %s", (user_id,))
        res = cursor.fetchone()
        if res:
            return User(id=res['email'], name=res['first_name'], email=res['email'], user_type='Registered')

        # [cite_start]Check Managers [cite: 16]
        cursor.execute("SELECT manager_id, first_name FROM Managers WHERE manager_id = %s", (user_id,))
        res = cursor.fetchone()
        if res:
            return User(id=res['manager_id'], name=res['first_name'], email=None, user_type='Manager')
    return None

def register_new_customer(data):
    """
    Backend logic for user signup.
    Inserts data into Registered_Customers and Customer_Phones.
    """
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


def get_flights_with_filters(user_type, date=None, source=None, destination=None):
    """
    Fetch flights with logic based on user type:
    - Customers/Guests: Only 'Active' flights.
    - Managers: All flights including cancelled/past.
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


def get_user_orders(email):
    """Fetches all orders for a registered user, including flight details[cite: 15, 85]."""
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



def get_order_by_code(order_code, email):
    """
    Fetches the total order details and all associated tickets.
    Returns a dictionary with 'info' (order data) and 'tickets' (list of tickets).
    """
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


def get_flight_seat_map(flight_id):
    """
    Returns the flight details and seat list
    Creata a seat map and checks which seats are occupied in flight  tickets
    """
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
