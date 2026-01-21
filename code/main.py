from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from utils import *
import os
from sql_queries import q1, q2, q3, q4, q5

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
    with db_cur() as cursor:
        cursor.execute("""
                UPDATE Flights 
                SET status = 'Arrived' 
                WHERE status = 'Active' 
                AND TIMESTAMP(departure_date, departure_time) < NOW()
            """)

    u_type = current_user.user_type if current_user.is_authenticated else 'Guest'  # Detect user type for flight dashboard visibility

    date = request.args.get('date')
    source = request.args.get('source')
    dest = request.args.get('dest')

    flights = get_flights_with_filters(u_type, date, source, dest)
    return render_template('homepage.html', flights=flights)


@app.route('/login', methods=['POST'])
def login():
    """
        Handles the authentication process for both Registered Customers and Managers.

        This function retrieves login credentials (ID/Email and Password) from the submitted form and attempts to
        verify them against the database. It supports a dual-login mechanism: checking the 'Registered_Customers'
        table first, and if no match is found, checking the 'Managers' table.

        Flow:
        1. Extract 'id_or_email' and 'password' from the HTTP POST request.
        2. Query the 'Registered_Customers' table.
        3. If not found, query the 'Managers' table.
        4. If a match is found in either:
           - Log the user in via Flask-Login.
           - Redirect to the homepage.
        5. If no match is found:
           - Flash an error message ('incorrect login details').
           - Redirect to the homepage.

        Returns:
           A redirect response to the homepage route ('/').
    """
    uid = request.form.get('id_or_email')
    pwd = request.form.get('password')

    with db_cur() as cursor:
        cursor.execute("SELECT email FROM Registered_Customers WHERE email=%s AND password=%s", (uid, pwd))
        user_data = cursor.fetchone()

        if not user_data:
            cursor.execute("SELECT manager_id FROM Managers WHERE manager_id=%s AND password=%s", (uid, pwd))
            user_data = cursor.fetchone()

        if user_data:
            user_id = user_data.get('email') or user_data.get('manager_id')
            login_user(get_user_by_id(user_id))
            return redirect(url_for('homepage'))
        else:
            # Part of project requirements: Flash message for incorrect details
            flash('incorrect login details', 'danger')
            return redirect(url_for('homepage'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Handles the new customer registration process.
    Supports both rendering the registration form and processing the data submission.

    Logic:
    1. Check Request Method:
       - If GET: Renders the 'signup.html' page.
       - If POST: Proceed to extraction.
    2. Data Extraction:
       - Converts standard form data to a dictionary.
    3. Backend Processing:
       - Calls `register_new_customer` to handle database insertion and validation.
    4. Response Handling:
       - Success: Flashes a success message and redirects to the homepage.
       - Failure: Flashes an error message and re-renders the form (allowing retry).

    Returns:
        A redirect response to the signup route (if method = GET)
        A redirect response to the homepage route (if method = POST)
    """
    if request.method == 'POST':
        customer_data = request.form.to_dict()

        customer_data['phones'] = request.form.getlist(
            'phone')  # multivalues attribute, we should be able to get numerous phone numbers

        success, message = register_new_customer(customer_data)
        if success:
            flash(message, "success")
            return redirect(url_for('homepage'))
        else:
            flash(message, "danger")
    return render_template('signup.html')


@app.route('/logout')
def logout():
    """ Handles the user/manager logout process """
    logout_user()
    return redirect(url_for('homepage'))


@app.template_filter('map_to_letter')
def map_to_letter(column_num):
    """
        A custom Jinja2 template filter designed to convert numeric column indices
        into standard airline seat letters (e.g., 1 -> 'A', 2 -> 'B').

        Args:
            column_num (int or str): The column number from the database/loop.

        Logic:
        1. Input Validation: Checks if the input is already a non-digit string (to prevent errors).
        2. Mapping: Uses a predefined dictionary to map integers 1 through 10
           to letters 'A' through 'J'.
        3. Fallback: If the number exceeds 10 or isn't found, returns the original input.

        Usage Example in HTML:
            {{ seat.column_num | map_to_letter }} -> Outputs 'A'

        Returns:
            str: The corresponding letter for the seat column.
        """
    if isinstance(column_num, str) and not column_num.isdigit():
        return column_num

    mapping = {
        1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F',
        7: 'G', 8: 'H', 9: 'I', 10: 'J'
    }
    return mapping.get(int(column_num), column_num)


@app.route('/book_flight/<string:flight_id>')
def book_flight(flight_id):
    """
        Initiates the booking process for a specific flight.

        Logic:
        1. Authorization Check: Blocks 'Manager' users from booking to prevent data corruption/conflict of interest.
        2. Data Retrieval: Calls `get_flight_seat_map` to fetch the flight details and the current status of all seats.
        3. Validation: If the flight ID is invalid, redirects to the homepage.

        Args:
            flight_id (str): The unique identifier of the flight.

        Returns:
            render_template: Renders 'booking.html' with the seat map and flight info.
    """

    if current_user.is_authenticated and current_user.user_type == 'Manager':
        flash("Managers cannot perform bookings.", "danger")
        return redirect(url_for('homepage'))

    flight_info, seats = get_flight_seat_map(flight_id)

    if not flight_info:
        flash("Flight not found.", "danger")
        return redirect(url_for('homepage'))

    return render_template('booking.html',
                           flight_id=flight_id,
                           all_seats=seats,
                           flight_info=flight_info)



@app.route('/manager/set_price', methods=['POST'])
@login_required
def set_flights_price():
    """
        Allows Managers to update ticket prices for Economy and Business classes.

        Logic:
        1. Authorization: Verifies the user is a 'Manager'.
        2. Input: Receives 'economy_price' and 'business_price' from the form.
        3. Database Update: Executes UPDATE queries on the 'Classes_In_Flights' table
           specifically for the given flight_id.

        Returns:
            redirect: Redirects to the homepage.
    """
    if current_user.user_type != 'Manager':
        flash("Unauthorized access", "danger")
        return redirect(url_for('homepage'))

    flight_id = request.form.get('flight_id')
    econ_price = float(request.form.get('economy_price'))
    biz_price = float(request.form.get('business_price'))

    with db_cur() as cursor:
        try:

            cursor.execute("""
                UPDATE Classes_In_Flights 
                SET price = %s 
                WHERE flight_id = %s AND class_type = 'Economy'
            """, (econ_price, flight_id))

            cursor.execute("""
                UPDATE Classes_In_Flights 
                SET price = %s 
                WHERE flight_id = %s AND class_type = 'Business'
            """, (biz_price, flight_id))

            flash(f"Prices for flight {flight_id} updated successfully!", "success")

        except Exception as e:
            flash(f"Error updating prices: {str(e)}", "danger")

    return redirect(url_for('homepage'))


@app.route('/mytrips')
@login_required
def my_trips():
    """
        Displays the personal flight history for a registered customer.

        Logic:
        1. Access Control: Restricts access to 'Registered' users only.
        2. Filtering: Extracts the 'status' parameter from the URL (e.g., ?status=Cancelled)
        to filter results (All/Active/Cancelled).
        3. Execution: Calls `get_customer_history` to fetch relevant orders.

        Returns:
            render_template: 'mytrips.html' with the list of orders and the filters.
    """

    if current_user.user_type != 'Registered':
        flash("Only registered customers have a saved history.", "warning")
        return redirect(url_for('homepage'))

    status_filter = request.args.get('status', 'All')
    orders = get_customer_history(current_user.email, status_filter)
    return render_template('mytrips.html', orders=orders, current_filter=status_filter)


@app.route('/cancel_order/<string:order_code>', methods=['POST'])
@login_required
def cancel_order(order_code):
    """
    Executes the cancellation action when the user clicks the button.

    Logic:
    1. Authorization: Verifies the user is 'Registered'.
    2. Retrieval: Calls 'cancel_order_transaction' to perform the transaction.

    Returns: redirect to my trips.

    """
    success, message = cancel_order_transaction(order_code)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for('my_trips'))


@app.route('/cancel_flight/<string:flight_id>', methods=['POST'])
@login_required
def cancel_flight(flight_id):
    """
        Allows a Manager to abort (cancel) an active flight.

        Logic:
        1. Authorization: Checks if current_user is a 'Manager'.
        2. Time Validation (Project requirements): Checks if the flight is more than 72 hours away.
           If it's closer than 72h, cancellation is blocked.
        3. Database Updates (Transaction):
           - Updates Flights table status to 'Cancelled'.
           - Updates all related Orders to 'Cancelled by system'.
           - Sets ticket prices to 0 (Simulating a full refund).

        Returns:
            redirect: Redirects to the homepage.
    """

    if current_user.user_type != 'Manager':
        flash("Unauthorized", "danger")
        return redirect(url_for('homepage'))

    with db_cur() as cursor:
        query = "SELECT departure_date, departure_time FROM Flights WHERE flight_id = %s"
        cursor.execute(query, (flight_id,))
        flight = cursor.fetchone()

        if not flight:
            flash("Flight not found", "danger")
            return redirect(url_for('homepage'))

        dept_dt = datetime.combine(flight['departure_date'], (datetime.min + flight['departure_time']).time())
        if (dept_dt - datetime.now()).total_seconds() < (72 * 3600):
            flash("Flights can only be cancelled at least 72 hours in advance.", "danger")
            return redirect(url_for('homepage'))

        try:
            cursor.execute("UPDATE Flights SET status = 'Cancelled' WHERE flight_id = %s", (flight_id,))
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


@app.route('/add_flight', methods=['GET', 'POST'])
@login_required
def add_flight():
    """
        Handles the multi-step process of adding a new flight to the system.
        Access is restricted to Managers based on task requirements.

        Logic:
        1. Step 1: Fetches available routes from 'Flight_Routes' to display selection.
        2. Step 2: Retrieves flight duration based on the selected route.
        3. Step 3: Validates input (Unique Flight ID and departure date, Date have not past, airplane existence, Runway availability).
           - Checks for runway conflicts within a 1-hour buffer.
           - Checks for resource availability (Planes, Pilots, Attendants).
        4. Finish: Commits the new flight and updates all resource mapping tables.

        Returns:
            render_template: Displays 'add_flight.html' with the relevant step data.
            redirect: Redirects to 'homepage' upon success or unauthorized access.
    """
    if current_user.user_type != 'Manager':
        flash("Unauthorized", "danger")
        return redirect(url_for('homepage'))

    step = request.form.get('step', '1')

    if step == '1':
        with db_cur() as cursor:
            cursor.execute("SELECT source_airport, destination_airport, flight_duration FROM Flight_Routes")
            routes = cursor.fetchall()
        return render_template('add_flight.html', step=1, routes=routes)

    elif step == '2':
        route_key = request.form.get('route_key')
        if not route_key:
            return redirect(url_for('add_flight'))

        source, dest = route_key.split('-')
        with db_cur() as cursor:
            cursor.execute(
                "SELECT flight_duration FROM Flight_Routes WHERE source_airport=%s AND destination_airport=%s",
                (source, dest))
            res = cursor.fetchone()
            duration = res['flight_duration']

        return render_template('add_flight.html', step=2, source=source, dest=dest, duration=duration)

    elif step == '3':
        f_id = request.form.get('flight_id')
        date = request.form.get('departure_date')
        time = request.form.get('departure_time')
        runway = request.form.get('runway_num')
        source = request.form.get('source')
        dest = request.form.get('dest')
        duration = int(request.form.get('duration'))

        try:
            flight_datetime_str = f"{date} {time}"
            flight_dt = datetime.strptime(flight_datetime_str, '%Y-%m-%d %H:%M')

            if flight_dt < datetime.now():
                flash("Error: You cannot add a flight in the past!", "danger")
                return render_template('add_flight.html', step=2, source=source, dest=dest, duration=duration,
                                       prev_fid=f_id, prev_date=date, prev_time=time, prev_runway=runway)
        except ValueError:
            flash("Invalid date or time format.", "danger")
            return render_template('add_flight.html', step=2, source=source, dest=dest, duration=duration,
                                   prev_fid=f_id, prev_date=date, prev_time=time, prev_runway=runway)

        if check_flight_id_exists(f_id):
            flash(f"Error: Flight ID '{f_id}' is already in use.", "danger")
            return render_template('add_flight.html', step=2, source=source, dest=dest, duration=duration,
                                   prev_fid=f_id, prev_date=date, prev_time=time, prev_runway=runway)

        with db_cur() as cursor:
            conflict_query = """
                SELECT flight_id, departure_time 
                FROM Flights 
                WHERE departure_date = %s 
                  AND runway_num = %s 
                  AND departure_time BETWEEN SUBTIME(%s, '01:00:00') AND ADDTIME(%s, '01:00:00')
            """
            cursor.execute(conflict_query, (date, runway, time, time))
            conflicts = cursor.fetchall()

            if conflicts:
                flash(
                    f"Error: Runway {runway} is busy within 1 hour of {time}. Conflicting flight(s): {[c['flight_id'] for c in conflicts]}",
                    "danger")
                return render_template('add_flight.html', step=2, source=source, dest=dest, duration=duration,
                                       prev_fid=f_id, prev_date=date, prev_time=time, prev_runway=runway)

        planes, pilots, attendants = get_available_resources(date, time, duration)

        is_long_haul = duration > 360
        req_pilots = 3 if is_long_haul else 2
        req_attendants = 6 if is_long_haul else 3

        if not planes:
            flash("No aircraft available for this time slot (all planes are busy or maintenance).", "danger")
            return render_template('add_flight.html', step=2, source=source, dest=dest, duration=duration,
                                   prev_fid=f_id, prev_date=date, prev_time=time, prev_runway=runway)

        if len(pilots) < req_pilots or len(attendants) < req_attendants:
            flash(f"Insufficient crew. Need {req_pilots} Pilots, {req_attendants} Attendants.", "danger")
            return render_template('add_flight.html', step=2, source=source, dest=dest, duration=duration,
                                   prev_fid=f_id, prev_date=date, prev_time=time, prev_runway=runway)

        return render_template('add_flight.html', step=3,
                               flight_id=f_id, departure_date=date, departure_time=time, runway_num=runway,
                               source=source, dest=dest, duration=duration,
                               planes=planes, pilots=pilots, attendants=attendants,
                               is_long_haul=is_long_haul)

    elif step == 'finish':
        success, msg = create_flight_final_step(request.form)

        if success:
            flash(msg, "success")
            return redirect(url_for('homepage'))
        else:
            flash(msg, "danger")
            # If failed, return to the begining of the form
            return redirect(url_for('add_flight'))

    return redirect(url_for('homepage'))


@app.route('/add_route', methods=['POST'])
@login_required
def add_route():
    """
        Handles the creation of a new flight route (Source -> Destination).
        Restricted to Managers.

        Logic:
        1. Access Control: Verifies the user is a Manager.
        2. Input Extraction: Gets source, destination, and duration from the form.
        3. Flow Control: Checks 'redirect_target' (hidden form field) to determine
           whether to return to the dashboard or the add-flight wizard after creation.
        4. Execution: Calls `create_new_route` to update the database.

        Returns:
            redirect: To the specified target URL (homepage or add_flight).
    """
    if current_user.user_type != 'Manager':
        flash("Unauthorized", "danger")
        return redirect(url_for('homepage'))

    source = request.form.get('source_airport').upper()
    dest = request.form.get('destination_airport').upper()
    duration = request.form.get('duration')

    redirect_target = request.form.get('redirect_target', 'homepage')

    success, message = create_new_route(source, dest, duration)

    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for(redirect_target))


@app.route('/order_summary', methods=['POST'])
def order_summary():
    """
        Calculates the final price and presents an invoice before the booking is committed.
        This acts as a "Checkout" page.

        Logic:
        1. Validation: Ensures at least one seat is selected.
        2. Price Calculation: Iterates through the selected seat keys (format: 'row-col-class-id'),
           fetches the specific price for each seat's class, and sums the total (uses get_current_price).
        3. Guest Handling: If the user is not logged in, temporarily captures their
           details from the previous form to pass to the final step.

        Returns:
            render_template: 'summary.html' containing the breakdown of costs.
    """

    flight_id = request.form.get('flight_id')
    selected_seats = request.form.getlist('selected_seats')

    if not selected_seats:
        flash("Please select at least one seat.", "warning")
        return redirect(url_for('book_flight', flight_id=flight_id))

    flight_info = get_flight_details(flight_id)

    total_price = 0
    parsed_seats = []
    for seat_key in selected_seats:
        row, col, s_class, airplane_id = seat_key.split('-', 3)
        price = get_current_price(flight_id, s_class)
        total_price += price
        parsed_seats.append({'row': row, 'col': col, 'class': s_class, 'price': price, 'key': seat_key})

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
    """
        Executes the final database transaction to create the order.
        Triggered after the user confirms the 'order_summary'.

        Logic:
        1. Data Re-collection: Retrieves flight ID and seat keys (passed via hidden fields
           in the summary page).
        2. Execution: Calls `create_booking` which handles the SQL INSERTs for
           Orders and Flight_Tickets tables.
        3. Success/Fail: Renders the confirmation ticket or returns to home on error.

        Returns:
            render_template: 'confirmation.html' with the new Order Code.
    """

    flight_id = request.form.get('flight_id')
    selected_seats = request.form.getlist('selected_seats')

    guest_data = None
    if not current_user.is_authenticated:
        guest_data = {
            'first_name': request.form.get('guest_first'),
            'last_name': request.form.get('guest_last'),
            'email': request.form.get('guest_email'),
            'phone': request.form.get('guest_phone')
        }

    success, message, order_code = create_booking(flight_id, selected_seats, current_user, guest_data)

    if success:
        return render_template('confirmation.html', order_code=order_code)
    else:
        flash(f"Booking failed: {message}", "danger")
        return redirect(url_for('homepage'))


@app.route('/manager/reports')
@login_required
def manager_reports():
    """
        Aggregates statistical data for the Manager Dashboard.

        Logic:
        1. Access Control: Enforces Manager-only access.
        2. Data Aggregation: Executes 5 distinct SQL queries to fetch:
           - Occupancy rates per flight.
           - Total revenue generation.
           - Crew activity logs.
           - Cancellation statistics.
           - Plane utilization/activity.

        Returns:
            render_template: 'reports.html' populated with the 'data' dictionary.
    """
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


@app.route('/guest_manage', methods=['GET', 'POST'])
def guest_manage():
    """
        Provides a portal for Unregistered Guests to view or cancel their specific orders.
        Authentication is done via Order Code + Email combination.

        Logic:
        1. GET Request: Renders the Guest Login form.
        2. POST Request (Authentication): Verifies if the Order Code matches the Email.
        3. Action 'View': Displays the order details ('guest_order.html').
        4. Action 'Cancel': Calls `cancel_order_transaction` to cancel the booking
           and calculates any applicable fees.

        Returns:
            render_template: The login form or the order management dashboard.
    """

    if request.method == 'POST':
        action = request.form.get('action')
        order_code = request.form.get('order_code')
        email = request.form.get('email')

        # 1. Attempt to fetch the order
        order_data = get_order_by_code(order_code, email)

        if not order_data:
            flash("Order not found or email does not match.", "danger")
            return redirect(url_for('guest_manage'))

        # 2. Handle Logic
        # FIX: If action is 'view' OR None (initial login), show the order page.
        if action == 'view' or action is None:
            return render_template('guest_order.html', order=order_data, email=email)

        elif action == 'cancel':
            success, msg = cancel_order_transaction(order_code)

            # Fetch updated data to show the new status
            updated_order = get_order_by_code(order_code, email)

            if success:
                flash(msg, "success")
            else:
                flash(msg, "danger")

            return render_template('guest_order.html', order=updated_order, email=email)

    return render_template('guest_login.html')


if __name__ == '__main__':
    # Running in debug mode for easier development
    app.run(debug=True)