import random
import string
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
    מחזיר את פרטי הטיסה ורשימת מושבים.
    מייצר מפת מושבים דינמית ובודק אילו מושבים תפוסים ב-Flight_Tickets.
    """
    with db_cur() as cursor:
        # 1. שליפת פרטי הטיסה והמטוס כדי לדעת כמה שורות יש [cite: 25]
        # הערה: אני מניח שיש עמודה airplane_id בטיסות וטבלה airplanes עם גודל.
        # אם אין, נצטרך להשתמש בלוגיקה של "גדול/קטן" מהדרישות.
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

        # 2. קביעת מספר שורות ומחלקות לפי סוג המטוס [cite: 24]
        # מטוס גדול: יש מחלקת עסקים. מטוס קטן: רק רגילה.
        # לצורך הדוגמה נגדיר: מטוס קטן=20 שורות (A-C, D-F), גדול=40 שורות.
        rows = 40 if flight['size'] else 20
        cols = ['A', 'B', 'C', 'D', 'E', 'F']

        # 3. בדיקת מושבים תפוסים
        cursor.execute("SELECT row_num, column_num FROM Flight_Tickets WHERE flight_id = %s", (flight_id,))
        taken_seats = {(r['row_num'], r['column_num']) for r in cursor.fetchall()}

        # 4. בניית רשימת המושבים ל-HTML
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


def create_booking(flight_id, seats, user, guest_data=None):
    """
    Create new booking and tickets
    """
    with db_cur() as cursor:
        try:
            # יצירת קוד הזמנה ייחודי
            order_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

            # זיהוי המזמין (מייל)
            email = user.email if user.is_authenticated else guest_data['email']

            # [cite: 38, 105] חישוב מחיר - בדוגמה זה פיקטיבי, בפועל יש לשלוף מחיר מהטיסה
            # נניח מחיר בסיס 100 לכרטיס
            price_per_ticket = 100

            # שמירת ההזמנה (Orders)
            cursor.execute("""
                INSERT INTO Orders (order_code, order_date, email, status)
                VALUES (%s, NOW(), %s, 'Active')
            """, (order_code, email))

            # שמירת הכרטיסים (Flight_Tickets)
            for seat in seats:
                row, col = seat.split('-')  # ה-HTML שולח "5-A"
                cursor.execute("""
                    INSERT INTO Flight_Tickets 
                    (order_code, flight_id, row_num, column_num, class_type, price)
                    VALUES (%s, %s, %s, %s, 'Economy', %s)
                """, (order_code, flight_id, row, col, price_per_ticket))

            # אם זה אורח, צריך לשמור פרטים בטבלאות רלוונטיות אם נדרש, או להסתמך על ההזמנה

            return True, "Success", order_code

        except mysql.connector.Error as err:
            return False, str(err), None