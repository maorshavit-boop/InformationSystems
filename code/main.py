from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from utils import *
import os

# Get the path to the project root (one level up from 'code' folder)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__,
            template_folder=os.path.join(project_root, 'templates'),
            static_folder=os.path.join(project_root, 'static'))

<<<<<<< HEAD
=======
app = Flask(__name__, template_folder='../templates', static_folder='../static')
>>>>>>> 19cb9ceac3a02af04f4fd0e3f4f41fe8fc7247f8
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
    # בדיקה למניעת ה-ValueError: אם זה כבר אות, פשוט תחזיר אותה
    if isinstance(column_num, str) and not column_num.isdigit():
        return column_num

    mapping = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F'}
    return mapping.get(int(column_num), column_num)


@app.route('/book_flight/<string:flight_id>')
def book_flight(flight_id):
    if current_user.is_authenticated and current_user.user_type == 'Manager':
        flash("Managers cannot perform bookings.", "danger")
        return redirect(url_for('homepage'))

    # חילוץ נתוני הטיסה והמושבים
    flight_info, seats = get_flight_seat_map(flight_id)

    if not flight_info:
        flash("Flight not found.", "danger")
        return redirect(url_for('homepage'))

    # שימוש ב-booking.html (במקום Flightseats.html)
    return render_template('booking.html',
                           flight_id=flight_id,
                           all_seats=seats,
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
        flash(f"Booking confirmed! Order Code: {order_code}", "success")
        return redirect(url_for('homepage'))  # או לדף תודה/הצגת כרטיס
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

if __name__ == '__main__':
    #Running in debug mode for easier development
    app.run(debug=True)

