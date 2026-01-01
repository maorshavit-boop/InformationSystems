from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from utils import *

app = Flask(__name__)
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
    """Handles both Manager and Customer login."""
    username = request.form.get('id_or_email')
    password = request.form.get('password')

    with db_cur() as cursor:
        # [cite_start]Check Customer [cite: 80]
        cursor.execute("SELECT email FROM Registered_Customers WHERE email=%s AND password=%s", (username, password))
        if cursor.fetchone():
            user = get_user_by_id(username)
            login_user(user)
            return redirect(url_for('homepage'))

        # [cite_start]Check Manager [cite: 16]
        cursor.execute("SELECT manager_id FROM Managers WHERE manager_id=%s AND password=%s", (username, password))
        # Note: Ensure you added a 'password' column to your Managers table if it's not in the original SQL
        if cursor.fetchone():
            user = get_user_by_id(username)
            login_user(user)
            return redirect(url_for('homepage'))

    flash('Invalid credentials')
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


@app.route('/book_flight/<string:flight_id>')
def book_flight(flight_id):
    #  Double Check managers can't order tickets
    if current_user.is_authenticated and current_user.user_type == 'Manager':
        flash("Managers cannot perform bookings.", "danger")
        return redirect(url_for('homepage'))
    # Extracting the seat map
    flight_data, seats = get_flight_seat_map(flight_id)
    if not flight_data:
        flash("Flight not found.", "danger")
        return redirect(url_for('homepage'))

    return render_template('Flightseats.html',
                           flight_id=flight_id,
                           all_seats=seats,
                           current_user=current_user)


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


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('homepage'))

if __name__ == '__main__':
    #Running in debug mode for easier development
    app.run(debug=True)

