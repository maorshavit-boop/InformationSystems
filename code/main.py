from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from utils import *
import os
from sql_queries import q1, q2, q3, q4, q5


# Get the path to the project root (one level up from 'code' folder)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__,
            template_folder=os.path.join(project_root, 'templates'),
            static_folder=os.path.join(project_root, 'static'))

app.secret_key = 'flytau_secret_key'

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'homepage'

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)


@app.route('/')
def homepage():
    # [cite_start]Detect user type for flight visibility [cite: 46]
    u_type = current_user.user_type if current_user.is_authenticated else 'Guest'

    # [cite_start]Get filters from request [cite: 45]
    date = request.args.get('date')
    source = request.args.get('source')
    dest = request.args.get('dest')

    flights = get_flights_with_filters(u_type, date, source, dest)
    return render_template('homepage.html', flights=flights)


@app.route('/login', methods=['POST'])
def login():
    uid = request.form.get('id_or_email')
    pwd = request.form.get('password')

    with db_cur() as cursor:
        # Check in Registered Customers
        cursor.execute("SELECT email FROM Registered_Customers WHERE email=%s AND password=%s", (uid, pwd))
        user_data = cursor.fetchone()

        # Check in Managers if not found in customers
        if not user_data:
            cursor.execute("SELECT manager_id FROM Managers WHERE manager_id=%s AND password=%s", (uid, pwd))
            user_data = cursor.fetchone()

        if user_data:
            user_id = user_data.get('email') or user_data.get('manager_id')
            login_user(get_user_by_id(user_id))
            return redirect(url_for('homepage'))
        else:
            # This is the requirement: Flash message for incorrect details
            flash('incorrect login details', 'danger')
            return redirect(url_for('homepage'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handles the signup process."""
    """Handles the signup process."""
    if request.method == 'POST':
        # Collect all form fields into a dictionary
        customer_data = request.form.to_dict()
        # Call the backend logic
        success, message = register_new_customer(customer_data)
        if success:
            flash(message, "success")
            return redirect(url_for('homepage'))
        else:
            flash(message, "danger")
    return render_template('signup.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('homepage'))

@app.template_filter('map_to_letter')
def map_to_letter(column_num):
    # בדיקה למניעת ה-ValueError
    if isinstance(column_num, str) and not column_num.isdigit():
        return column_num

    # הוספתי מיפוי לעמודות 7, 8, 9, 10
    mapping = {
        1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F',
        7: 'G', 8: 'H', 9: 'I', 10: 'J'
    }
    return mapping.get(int(column_num), column_num)


@app.route('/book_flight/<string:flight_id>')
def book_flight(flight_id):
    # 1. בדיקת הרשאות (מנהלים לא מזמינים)
    if current_user.is_authenticated and current_user.user_type == 'Manager':
        flash("Managers cannot perform bookings.", "danger")
        return redirect(url_for('homepage'))

    # 2. חילוץ נתוני הטיסה והמושבים (חובה לבצע זאת לפני הבדיקה!)
    flight_info, seats = get_flight_seat_map(flight_id)

    # 3. בדיקה אם הטיסה קיימת
    if not flight_info:
        flash("Flight not found.", "danger")
        return redirect(url_for('homepage'))

    # 4. הצגת הדף
    return render_template('booking.html',
                           flight_id=flight_id,
                           all_seats=seats,   # מעביר את אובייקט המושבים המורכב (מילון)
                           flight_info=flight_info)


@app.route('/complete_booking', methods=['POST'])
def complete_booking():
    # Data collection from forms
    flight_id = request.form.get('flight_id')
    selected_seats = request.form.getlist('selected_seats')  # gets a list in format ['1-A', '2-B']

    if not selected_seats:
        flash("Please select at least one seat.", "warning")
        return redirect(url_for('book_flight', flight_id=flight_id))

    # Distinguish between an unregistered customer to a registered customer
    guest_details = None
    if not current_user.is_authenticated:
        guest_details = {
            'first_name': request.form.get('guest_first'),
            'last_name': request.form.get('guest_last'),
            'email': request.form.get('guest_email'),
            'phone': request.form.get('guest_phone')
        }

    # Execution of the order in the DB
    success, message, order_code = create_booking(flight_id, selected_seats, current_user, guest_details)

    if success:
        # במקום redirect ל-homepage, נשלח לדף אישור עם קוד ההזמנה
        return render_template('confirmation.html', order_code=order_code)
    else:
        flash(f"Booking failed: {message}", "danger")
        return redirect(url_for('book_flight', flight_id=flight_id))


@app.route('/manager/set_price', methods=['POST'])
@login_required
def set_flights_price():
    """Allows managers to determine the price for a flight and class."""
    if current_user.user_type != 'Manager':
        flash("Unauthorized access", "danger")
        return redirect(url_for('homepage'))

    flight_id = request.form.get('flight_id')
    econ_price = float(request.form.get('economy_price', 150.00))
    biz_price = float(request.form.get('business_price', 350.00))

    # Save to our global dictionary
    MANAGER_PRICES[flight_id] = {
        'Economy': econ_price,
        'Business': biz_price
    }

    flash(f"Prices for flight {flight_id} updated successfully!", "success")
    return redirect(url_for('homepage')) # Or manager dashboard

@app.route('/mytrips')
@login_required
def my_trips():
    """Displays the order history for the registered user."""
    # Ensure only registered users can access this page
    if current_user.user_type != 'Registered':
        flash("Only registered customers have a saved history.", "warning")
        return redirect(url_for('homepage'))

    # Fetch data using the utility function
    orders = get_customer_history(current_user.email)
    return render_template('mytrips.html', orders=orders)


@app.route('/cancel_order/<string:order_code>', methods=['POST'])
@login_required
def cancel_order(order_code):
    """Executes the cancellation action when the user clicks the button."""
    success, message = cancel_order_transaction(order_code)

    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for('my_trips'))


@app.route('/cancel_flight/<string:flight_id>', methods=['POST'])
@login_required
def cancel_flight(flight_id):
    if current_user.user_type != 'Manager':
        flash("Unauthorized", "danger")
        return redirect(url_for('homepage'))

    with db_cur() as cursor:
        # [cite_start]1. בדיקת ה-72 שעות לפני הביטול
        query = "SELECT departure_date, departure_time FROM Flights WHERE flight_id = %s"
        cursor.execute(query, (flight_id,))
        flight = cursor.fetchone()

        if not flight:
            flash("Flight not found", "danger")
            return redirect(url_for('homepage'))

        # שילוב תאריך ושעה לבדיקת הזמן שנותר
        dept_dt = datetime.combine(flight['departure_date'], (datetime.min + flight['departure_time']).time())
        if (dept_dt - datetime.now()).total_seconds() < (72 * 3600):
            flash("Flights can only be cancelled at least 72 hours in advance.", "danger")
            return redirect(url_for('homepage'))

        try:
            # [cite_start]2. עדכון סטטוס הטיסה [cite: 47]
            cursor.execute("UPDATE Flights SET status = 'Cancelled' WHERE flight_id = %s", (flight_id,))

            # [cite_start]3. זיכוי מלא לכל ההזמנות הפעילות (עדכון ל-0 ש"ח) [cite: 47]
            cursor.execute("""
                UPDATE Orders O
                JOIN Flight_Tickets FT ON O.order_code = FT.order_code
                SET O.status = 'Cancelled by system', FT.price = 0
                WHERE FT.flight_id = %s AND O.status = 'Active'
            """, (flight_id,))

            flash(f"Flight {flight_id} cancelled and customers refunded.", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    return redirect(url_for('homepage'))


@app.route('/add_flight', methods=['POST'])
@login_required
def add_flight():
    if current_user.user_type != 'Manager':
        flash("Unauthorized", "danger")
        return redirect(url_for('homepage'))

    # חילוץ נתונים מהטופס
    f_id = request.form.get('flight_id')
    f_date = request.form.get('departure_date')
    f_time = request.form.get('departure_time')
    plane_id = request.form.get('airplane_id')
    origin = request.form.get('source_airport')
    dest = request.form.get('destination_airport')
    runway = request.form.get('runway_num')

    with db_cur() as cursor:
        try:
            # הוספת הטיסה לפי הסכימה: flight_id, departure_date, airplane_id, source, destination, status, time, runway
            sql = """
                INSERT INTO Flights (flight_id, departure_date, airplane_id, source_airport, destination_airport, status, departure_time, runway_num)
                VALUES (%s, %s, %s, %s, %s, 'Active', %s, %s)
            """
            cursor.execute(sql, (f_id, f_date, plane_id, origin, dest, f_time, runway))
            flash("Flight added successfully!", "success")
        except Exception as e:
            flash(f"Error adding flight: {str(e)}", "danger")

    return redirect(url_for('homepage'))


# main.py

@app.route('/order_summary', methods=['POST'])
def order_summary():
    """Displays a summary of the order including total price before final confirmation."""
    flight_id = request.form.get('flight_id')
    selected_seats = request.form.getlist('selected_seats')  # Format: 'row-col-class-airplane_id'

    if not selected_seats:
        flash("Please select at least one seat.", "warning")
        return redirect(url_for('book_flight', flight_id=flight_id))

    # Get flight details for the summary
    flight_info = get_flight_details(flight_id)

    # Calculate total price and parse seat info for display
    total_price = 0
    parsed_seats = []
    for seat_key in selected_seats:
        row, col, s_class, airplane_id = seat_key.split('-',3)
        # [cite_start]Using the utility function to get price
        price = get_current_price(flight_id, s_class)
        total_price += price
        parsed_seats.append({'row': row, 'col': col, 'class': s_class, 'price': price, 'key': seat_key})

    # Guest details if not authenticated
    guest_details = {}
    if not current_user.is_authenticated:
        guest_details = {
            'first_name': request.form.get('guest_first'),
            'last_name': request.form.get('guest_last'),
            'email': request.form.get('guest_email'),
            'phone': request.form.get('guest_phone')
        }

    return render_template('summary.html',
                           flight=flight_info,
                           seats=parsed_seats,
                           total=total_price,
                           guest=guest_details)


@app.route('/finalize_booking', methods=['POST'])
def finalize_booking():
    """Executes the final database transaction."""
    flight_id = request.form.get('flight_id')
    # Re-collect selected seat keys from the hidden inputs in summary.html
    selected_seats = request.form.getlist('selected_seats')

    guest_data = None
    if not current_user.is_authenticated:
        guest_data = {
            'first_name': request.form.get('guest_first'),
            'last_name': request.form.get('guest_last'),
            'email': request.form.get('guest_email'),
            'phone': request.form.get('guest_phone')
        }

    # [cite_start]Perform the DB insertion
    success, message, order_code = create_booking(flight_id, selected_seats, current_user, guest_data)

    if success:
        return render_template('confirmation.html', order_code=order_code)
    else:
        flash(f"Booking failed: {message}", "danger")
        return redirect(url_for('homepage'))

@app.route('/manager/reports')
@login_required
def manager_reports():
        # to block who is not manager
    if current_user.user_type != 'Manager':
        flash("Access Denied: Managers Only", "danger")
        return redirect(url_for('homepage'))

    data = {}
    with db_cur() as cursor:
        cursor.execute(q1)
        data['occupancy'] = cursor.fetchall()
        cursor.execute(q2)
        data['revenue'] = cursor.fetchall()

        cursor.execute(q3)
        data['crew'] = cursor.fetchall()

        cursor.execute(q4)
        data['cancellations'] = cursor.fetchall()

        cursor.execute(q5)
        data['plane_activity'] = cursor.fetchall()

    return render_template('reports.html', data=data)


if __name__ == '__main__':
    #Running in debug mode for easier development
    app.run(debug=True)

