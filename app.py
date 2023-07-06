from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import psycopg2
from sqlalchemy import func

app = Flask(__name__)
app.secret_key = "SamJoshua"  # Set your secret key for session management

# Configure PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://samjoshua:oYsCZkCLjHBKaVzwMFldCqcRQete1yKd@dpg-cij8f215rnut2sbceppg-a.oregon-postgres.render.com/flight_jqwj'
db = SQLAlchemy(app)

# Define the models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    bookings = db.relationship('Booking', backref='user', lazy=True)

class Flight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(255), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    total_seats = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    arrival_name = db.Column(db.String(255), nullable=False)
    departure_name = db.Column(db.String(255), nullable=False)
    bookings = db.relationship('Booking', backref='flight', lazy=True)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flight.id'), nullable=True)
    no_of_ticket = db.Column(db.Integer, nullable=False)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

def check_database_tables():
    with app.app_context():
        try:
            conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
            conn.autocommit = True
            cursor = conn.cursor()

            # Check if the tables exist in the database
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user')")
            user_table_exists = cursor.fetchone()[0]

            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'flight')")
            flight_table_exists = cursor.fetchone()[0]

            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'booking')")
            booking_table_exists = cursor.fetchone()[0]

            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'employee')")
            employee_table_exists = cursor.fetchone()[0]

            # If the tables do not exist, create them
            if not user_table_exists:
                db.create_all()

            if not flight_table_exists:
                db.create_all()

            if not booking_table_exists:
                db.create_all()

            if not employee_table_exists:
                db.create_all()

            cursor.close()
            conn.close()

        except psycopg2.Error as e:
            print(f"Error checking database tables: {e}")
# Routes for user functionality
@app.route('/')
def home():
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handle login authentication
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin':
            session['admin'] = username
            return redirect('/admin/dashboard')
        
        # Perform authentication logic here (check credentials against User table)
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = username
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Handle sign up logic and create a new user in the User table
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        full_name = request.form['full_name']

        # Check if the user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('signup.html', error='Username already exists')

        # Validate password length
        if len(password) < 7:
            return render_template('signup.html', error='Password must be at least 7 characters long')

        # Create a new user instance
        new_user = User(username=username, password=password, email=email, full_name=full_name)

        # Add the new user to the session and commit the changes to the database
        db.session.add(new_user)
        db.session.commit()

        return redirect('/login')

    return render_template('signup.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect('/login')

    if request.method == 'POST':
        date = request.form['date']
        # Perform flight search logic based on the selected date
        flights = Flight.query.filter(func.date_trunc('day', Flight.departure_time) == date).all()
        return render_template('dashboard.html', flights=flights)

    return render_template('dashboard.html')

@app.route('/dashboard/user')
def user_dashboard():
    if 'username' not in session:
        return redirect('/login')

    username = session['username']
    user = User.query.filter_by(username=username).first()
    bookings = Booking.query.filter_by(user_id=user.id).all()
    return render_template('user_dashboard.html', bookings=bookings)



@app.route('/book_flight/<int:flight_id>', methods=['GET', 'POST'])
def book_flight(flight_id):
    flight = Flight.query.get(flight_id)

    if request.method == 'POST':
        # Get the number of tickets from the form
        num_tickets = int(request.form['num_tickets'])

        # Check if there are enough available seats
        if num_tickets <= flight.available_seats:
            # Update the available seats count
            flight.available_seats -= num_tickets
            db.session.commit()

            # Retrieve the user based on the currently logged-in user's username
            username = session.get('username')
            user = User.query.filter_by(username=username).first()

            # Create a booking entry with the retrieved user_id
            new_booking = Booking(user_id=user.id, flight_id=flight_id, no_of_ticket=num_tickets)
            db.session.add(new_booking)
            db.session.commit()

            return redirect('/dashboard')
        else:
            return render_template('ticket_counter.html', flight=flight, error='Not enough available seats')

    return render_template('ticket_counter.html', flight=flight)



@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        employee = Employee.query.filter_by(name=username, password=password).first()
        if employee:
            session['admin'] = username
            return redirect('/admin/dashboard')
        else:
            return render_template('admin_login.html', error='Invalid credentials')

    return render_template('admin_login.html')

@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        # Handle admin sign up logic and create a new employee in the Employee table
        username = request.form['username']
        password = request.form['password']

        # Check if the employee already exists
        existing_employee = Employee.query.filter_by(name=username).first()
        if existing_employee:
            return render_template('admin_signup.html', error='Username already exists')

        # Create a new employee instance
        new_employee = Employee(name=username, password=password)

        # Add the new employee to the session and commit the changes to the database
        db.session.add(new_employee)
        db.session.commit()

        return redirect('/admin/login')

    return render_template('admin_signup.html')

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin/login')

    if request.method == 'POST':
        # Create a new flight
        flight_number = request.form['flight_number']
        departure_time = request.form['departure_time']
        total_seats = request.form['total_seats']
        available_seats = request.form['available_seats']
        arrival_name = request.form['arrival_name']
        departure_name = request.form['departure_name']

        new_flight = Flight(flight_number=flight_number, departure_time=departure_time,
                            total_seats=total_seats, available_seats=available_seats,
                            arrival_name=arrival_name, departure_name=departure_name)
        db.session.add(new_flight)
        db.session.commit()

        return redirect('/admin/dashboard')

    else:
        flights = Flight.query.all()
        return render_template('admin_dashboard.html', flights=flights)
        

@app.route('/create_flight', methods=['GET', 'POST'])
def create_flight():
    if 'admin' not in session:
        return redirect('/admin/login')

    if request.method == 'POST':
        # Create a new flight
        flight_number = request.form['flight_number']
        departure_time = request.form['departure_time']
        total_seats = request.form['total_seats']
        available_seats = total_seats 
        arrival_name = request.form['arrival_name']
        departure_name = request.form['departure_name']

        new_flight = Flight(flight_number=flight_number, departure_time=departure_time,
                            total_seats=total_seats, available_seats=available_seats,
                            arrival_name=arrival_name, departure_name=departure_name)
        db.session.add(new_flight)
        db.session.commit()

        return redirect('/admin/dashboard')

    return render_template('create_flight.html')



@app.route('/admin/get_flight/<int:flight_id>', methods=['GET'])
def get_flight(flight_id):
    flight = Flight.query.get(flight_id)
    return render_template('flight_info.html', flight=flight)

@app.route('/admin/edit_flight/<int:flight_id>', methods=['GET', 'POST'])
def edit_flight(flight_id):
    flight = Flight.query.get(flight_id)

    if request.method == 'POST':
        # Update the flight information
        flight.flight_number = request.form['flight_number']
        flight.departure_time = request.form['departure_time']
        flight.total_seats = request.form['total_seats']
        flight.available_seats = request.form['available_seats']
        flight.arrival_name = request.form['arrival_name']
        flight.departure_name = request.form['departure_name']
        db.session.commit()
        return redirect('/admin/dashboard')

    return render_template('edit_flight.html', flight=flight)


@app.route('/admin/delete_flight/<int:flight_id>', methods=['POST'])
def delete_flight(flight_id):
    flight = Flight.query.get(flight_id)
    if not flight:
        return redirect('/admin/dashboard')  # Flight not found, redirect to dashboard

    # Update associated bookings
    bookings = Booking.query.filter_by(flight_id=flight.id).all()
    # Delete the associated bookings
    for booking in bookings:
        db.session.delete(booking)

    # Delete the flight
    db.session.delete(flight)
    db.session.commit()

    return redirect('/admin/dashboard')



@app.route('/admin')
def redirect_dashboard():
    if 'admin' not in session:
        return redirect('/admin/login')
    else:
        return redirect('/admin/dashboard')

@app.route('/users')
def show_users():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/admins')
def show_admins():
    admins = Employee.query.all()
    return render_template('admins.html', admins=admins)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        # Perform logout logic
        session.clear()
        return redirect('/login')

    # For GET requests, redirect to the login page
    return redirect('/login')


if __name__ == '__main__':
    check_database_tables()
    app.run(host="0.0.0.0") 
