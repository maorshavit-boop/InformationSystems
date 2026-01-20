DROP SCHEMA IF EXISTS FLYTAU;

CREATE SCHEMA FLYTAU;

USE FLYTAU;

-- 1. Pilots table
CREATE TABLE Pilots (
    pilot_id VARCHAR(20) PRIMARY KEY,
    first_name VARCHAR(50),
    middle_name VARCHAR(50),
    last_name VARCHAR(50),
    city VARCHAR(50),
    street VARCHAR(50),
    house_num VARCHAR(10),
    start_date DATE,
    long_flight_training BOOLEAN
);

-- 2. Flight Attendants table
CREATE TABLE Flight_Attendants (
    attendant_id VARCHAR(20) PRIMARY KEY,
    first_name VARCHAR(50),
    middle_name VARCHAR(50),
    last_name VARCHAR(50),
    city VARCHAR(50),
    street VARCHAR(50),
    house_num VARCHAR(10),
    start_date DATE,
    long_flight_training BOOLEAN
);

-- 3. Managers table
CREATE TABLE Managers (
    manager_id VARCHAR(20) PRIMARY KEY,
    password VARCHAR(25),
    first_name VARCHAR(50),
    middle_name VARCHAR(50),
    last_name VARCHAR(50),
    city VARCHAR(50),
    street VARCHAR(50),
    house_num VARCHAR(10),
    start_date DATE
);

-- 4. Pilot Phones table
CREATE TABLE Pilot_Phones (
    phone_num VARCHAR(20),
    pilot_id VARCHAR(20),
    PRIMARY KEY (phone_num, pilot_id),
    FOREIGN KEY (pilot_id) REFERENCES Pilots(pilot_id)
);

-- 5. Manager Phones table
CREATE TABLE Manager_Phones (
    phone_num VARCHAR(20),
    manager_id VARCHAR(20),
    PRIMARY KEY (phone_num, manager_id),
    FOREIGN KEY (manager_id) REFERENCES Managers(manager_id)
);

-- 6. Flight Attendant Phones table
CREATE TABLE Attendant_Phones (
    phone_num VARCHAR(20),
    attendant_id VARCHAR(20),
    PRIMARY KEY (phone_num, attendant_id),
    FOREIGN KEY (attendant_id) REFERENCES Flight_Attendants(attendant_id)
);

-- 7. Flight Routes table
CREATE TABLE Flight_Routes (
    source_airport VARCHAR(50),
    destination_airport VARCHAR(50),
    flight_duration INT, -- flight duration in minutes
    PRIMARY KEY (source_airport, destination_airport)
);

-- 8. Airplanes table
CREATE TABLE Airplanes (
    airplane_id VARCHAR(20) PRIMARY KEY,
    manufacturer VARCHAR(50),
    purchase_date DATE,
    size ENUM('Small','Big') -- Only these values allowed
);

-- 9. Flights table
CREATE TABLE Flights (
    flight_id VARCHAR(20),
    departure_date DATE,
    airplane_id VARCHAR(20),
    source_airport VARCHAR(50),
    destination_airport VARCHAR(50),
    status ENUM('Active','Full Capacity','Arrived', 'Cancelled'),
    departure_time TIME,
    runway_num ENUM('R1','R2', 'R3', 'R4', 'R5'),
    PRIMARY KEY (flight_id, departure_date),
    FOREIGN KEY (airplane_id) REFERENCES Airplanes(airplane_id),
    FOREIGN KEY (source_airport, destination_airport) REFERENCES Flight_Routes(source_airport, destination_airport)
);

-- 10. Pilots In Flights table
CREATE TABLE Pilots_In_Flights (
    pilot_id VARCHAR(20),
    flight_id VARCHAR(20),
    departure_date DATE,
    PRIMARY KEY (pilot_id, flight_id),
    FOREIGN KEY (pilot_id) REFERENCES Pilots(pilot_id),
    FOREIGN KEY (flight_id, departure_date) REFERENCES Flights(flight_id, departure_date)
);

-- 11. Attendants In Flights table
CREATE TABLE Attendants_In_Flights (
    attendant_id VARCHAR(20),
    departure_date DATE,
    flight_id VARCHAR(20),
    PRIMARY KEY (attendant_id, flight_id),
    FOREIGN KEY (attendant_id) REFERENCES Flight_Attendants(attendant_id),
    FOREIGN KEY (flight_id, departure_date) REFERENCES Flights(flight_id, departure_date)
);

-- 12. Airplane Classes table weak entity
CREATE TABLE Airplane_Classes (
    class_type ENUM('Economy','Business'),
    airplane_id VARCHAR(20),
    columns_count INT,
    rows_count INT,
    PRIMARY KEY (class_type, airplane_id),
    FOREIGN KEY (airplane_id) REFERENCES Airplanes(airplane_id) ON DELETE CASCADE
);

-- 13. Classes in flights 
CREATE TABLE Classes_In_Flights (
	flight_id VARCHAR(20),
	departure_date DATE,
	class_type ENUM('Economy','Business'),
    airplane_id VARCHAR(20),
	price FLOAT,
	PRIMARY KEY (flight_id, departure_date, class_type, airplane_id),
	FOREIGN KEY (flight_id, departure_date) REFERENCES Flights(flight_id, departure_date) ON DELETE CASCADE,
	FOREIGN KEY (class_type, airplane_id) REFERENCES Airplane_Classes(class_type, airplane_id) ON DELETE CASCADE
);

-- 14. Seats table - weak entity
CREATE TABLE Seats (
    row_num INT,
    column_num INT,
    class_type ENUM('Economy','Business'),
    airplane_id VARCHAR(20),
    PRIMARY KEY (row_num, column_num, class_type, airplane_id),
    FOREIGN KEY (class_type, airplane_id) REFERENCES Airplane_Classes(class_type, airplane_id) ON DELETE CASCADE
);

-- 15. Registered Customers table
CREATE TABLE Registered_Customers (
    email VARCHAR(100) PRIMARY KEY,
    first_name VARCHAR(50),
    middle_name VARCHAR(50),
    last_name VARCHAR(50),
    passport_num VARCHAR(20),
    registration_date DATE,
    birth_date DATE,
    password VARCHAR(100),
    customer_type ENUM('Registered')
);

-- 16. Unregistered Customers table
CREATE TABLE Unregistered_Customers (
    email VARCHAR(100) PRIMARY KEY,
    first_name VARCHAR(50),
    middle_name VARCHAR(50),
    last_name VARCHAR(50),
    customer_type ENUM('Unregistered')
);

-- 17. Customer Phones table
CREATE TABLE Customer_Phones (
    phone_num VARCHAR(20) PRIMARY KEY,
    email VARCHAR(100), -- Logical link to Customers
    customer_type ENUM('Registered','Unregistered') -- Indicates which table to check ('Registered'/'Unregistered')
);

-- 18. Orders table
CREATE TABLE Orders (
    order_code VARCHAR(20) PRIMARY KEY,
    customer_email VARCHAR(100), -- Logical link to Customers
    status ENUM('Active', 'Executed','Cancelled by customer', 'Cancelled by system'),
    order_date DATE,
    customer_type ENUM('Registered','Unregistered') -- Indicates which table to check ('Registered'/'Unregistered')
);


-- 19. Flight Tickets table
CREATE TABLE Flight_Tickets (
    order_code VARCHAR(20),
    flight_id VARCHAR(20),
    departure_date DATE,
    row_num INT,
    column_num INT,
    class_type ENUM('Economy','Business'),
    airplane_id VARCHAR(20),
    price DECIMAL (10 , 2),
    PRIMARY KEY (order_code, flight_id, departure_date, row_num, column_num, class_type),
    FOREIGN KEY (order_code) REFERENCES Orders(order_code),
    FOREIGN KEY (flight_id, departure_date) REFERENCES Flights(flight_id, departure_date),
    FOREIGN KEY (row_num, column_num, class_type, airplane_id) REFERENCES Seats(row_num, column_num, class_type, airplane_id)
);