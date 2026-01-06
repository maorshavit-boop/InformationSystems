USE FLYTAU;

-- ==========================================================
-- 1. INFRASTRUCTURE: ROUTES & AIRPLANES (6 Planes required)
-- ==========================================================

-- Inserting Routes (Long > 6 hours, Short <= 6 hours)
INSERT INTO Flight_Routes (source_airport, destination_airport, flight_duration) VALUES
('TLV', 'JFK', 660), -- Long
('JFK', 'TLV', 630), -- Long
('TLV', 'LHR', 330), -- Short
('TLV', 'ETM', 45), -- Short
('TLV', 'CDG', 290); -- Short

-- Inserting 6 Airplanes (Mix of Manufacturers & Sizes) [cite: 41, 120]
INSERT INTO Airplanes (airplane_id, manufacturer, purchase_date, size) VALUES
('AP-B787-1', 'Boeing', '2020-01-01', 'Big'),   -- Big Plane 1
('AP-B737-2', 'Boeing', '2019-05-15', 'Small'), -- Small Plane 1
('AP-A380-3', 'Airbus', '2021-11-20', 'Big'),   -- Big Plane 2
('AP-A320-4', 'Airbus', '2018-03-10', 'Small'), -- Small Plane 2
('AP-F7X-5',  'Dassault','2022-07-01', 'Small'), -- Small Plane 3 (Falcon)
('AP-F10X-6', 'Dassault','2023-01-01', 'Big');   -- Big Plane 3 (Hypothetical big Dassault for schema logic)

-- Inserting Classes for the 6 Airplanes
-- Big planes have Economy + Business. Small planes have Economy only. [cite: 43]
INSERT INTO Airplane_Classes (class_type, airplane_id, columns_count, rows_count) VALUES
('Business', 'AP-B787-1', 4, 5), ('Economy', 'AP-B787-1', 9, 30),
('Economy',  'AP-B737-2', 6, 25),
('Business', 'AP-A380-3', 6, 10), ('Economy', 'AP-A380-3', 10, 40),
('Economy',  'AP-A320-4', 6, 25),
('Economy',  'AP-F7X-5',  4, 15),
('Business', 'AP-F10X-6', 4, 5), ('Economy', 'AP-F10X-6', 6, 20);

-- Inserting Sample Seats (Required for tickets)
-- We populate seat (1,1) for all planes to ensure ticket creation works
INSERT INTO Seats (row_num, column_num, class_type, airplane_id) VALUES
(1, 1, 'Business', 'AP-B787-1'), (1, 2, 'Business', 'AP-B787-1'),
(10, 1, 'Economy', 'AP-B787-1'),
(1, 1, 'Economy',  'AP-B737-2'),
(1, 1, 'Business', 'AP-A380-3'),
(1, 1, 'Economy',  'AP-A320-4');

-- ==========================================================
-- 2. STAFF (2 Managers, 10 Pilots, 20 Attendants) 
-- ==========================================================

-- 2 Managers
INSERT INTO Managers (manager_id, first_name, last_name, city, start_date) VALUES
('M-001', 'Sarah', 'Connor', 'Tel Aviv', '2015-01-01'),
('M-002', 'Tony', 'Stark', 'Herzliya', '2016-06-15');

INSERT INTO Manager_Phones (phone_num, manager_id) VALUES
('050-1000001', 'M-001'), ('050-1000002', 'M-002');

-- 10 Pilots (Some with long flight training)
INSERT INTO Pilots (pilot_id, first_name, last_name, start_date, long_flight_training) VALUES
('P-001', 'Maverick', 'Mitchell', '2010-01-01', TRUE),
('P-002', 'Iceman', 'Kazansky', '2011-02-01', TRUE),
('P-003', 'Amelia', 'Earhart', '2012-03-01', TRUE),
('P-004', 'Chuck', 'Yeager', '2013-04-01', TRUE),
('P-005', 'Sully', 'Sullenberger', '2014-05-01', TRUE),
('P-006', 'Han', 'Solo', '2020-01-01', FALSE), -- Short flights only
('P-007', 'Wedge', 'Antilles', '2021-01-01', FALSE),
('P-008', 'Starbuck', 'Thrace', '2022-01-01', FALSE),
('P-009', 'Apollo', 'Adama', '2023-01-01', FALSE),
('P-010', 'Fox', 'McCloud', '2024-01-01', FALSE);

-- Pilot Phones (1 per pilot)
INSERT INTO Pilot_Phones (phone_num, pilot_id) VALUES
('052-2000001', 'P-001'), ('052-2000002', 'P-002'), ('052-2000003', 'P-003'),
('052-2000004', 'P-004'), ('052-2000005', 'P-005'), ('052-2000006', 'P-006'),
('052-2000007', 'P-007'), ('052-2000008', 'P-008'), ('052-2000009', 'P-009'),
('052-2000010', 'P-010');

-- 20 Flight Attendants
INSERT INTO Flight_Attendants (attendant_id, first_name, last_name, start_date, long_flight_training) VALUES
('FA-001', 'Rachel', 'Green', '2018-01-01', TRUE),
('FA-002', 'Monica', 'Geller', '2018-02-01', TRUE),
('FA-003', 'Phoebe', 'Buffay', '2018-03-01', TRUE),
('FA-004', 'Joey', 'Tribbiani', '2018-04-01', TRUE),
('FA-005', 'Chandler', 'Bing', '2018-05-01', TRUE),
('FA-006', 'Ross', 'Geller', '2018-06-01', TRUE),
('FA-007', 'Jerry', 'Seinfeld', '2019-01-01', FALSE),
('FA-008', 'Elaine', 'Benes', '2019-02-01', FALSE),
('FA-009', 'George', 'Costanza', '2019-03-01', FALSE),
('FA-010', 'Cosmo', 'Kramer', '2019-04-01', FALSE),
('FA-011', 'Ted', 'Mosby', '2020-01-01', FALSE),
('FA-012', 'Robin', 'Scherbatsky', '2020-02-01', FALSE),
('FA-013', 'Barney', 'Stinson', '2020-03-01', FALSE),
('FA-014', 'Lily', 'Aldrin', '2020-04-01', FALSE),
('FA-015', 'Marshall', 'Eriksen', '2020-05-01', FALSE),
('FA-016', 'Michael', 'Scott', '2021-01-01', FALSE),
('FA-017', 'Dwight', 'Schrute', '2021-02-01', FALSE),
('FA-018', 'Jim', 'Halpert', '2021-03-01', FALSE),
('FA-019', 'Pam', 'Beesly', '2021-04-01', FALSE),
('FA-020', 'Ryan', 'Howard', '2021-05-01', FALSE);

-- Attendant Phones (Sample)
INSERT INTO Attendant_Phones (phone_num, attendant_id) VALUES
('054-3000001', 'FA-001'), ('054-3000002', 'FA-002'), ('054-3000007', 'FA-007');

-- ==========================================================
-- 3. CUSTOMERS (2 Registered, 2 Guests) 
-- ==========================================================

INSERT INTO Registered_Customers (email, first_name, last_name, passport_num, registration_date, birth_date, password, customer_type) VALUES
('reg1@test.com', 'Alice', 'Wonderland', 'PASS1001', '2023-01-01', '1990-05-05', 'pass123', 'Registered'),
('reg2@test.com', 'Bob', 'Builder', 'PASS1002', '2023-06-01', '1985-08-08', 'buildit', 'Registered');

INSERT INTO Unregistered_Customers (email, first_name, last_name, customer_type) VALUES
('guest1@test.com', 'Charlie', 'Chaplin', 'Unregistered'),
('guest2@test.com', 'Marilyn', 'Monroe', 'Unregistered');

INSERT INTO Customer_Phones (phone_num, email, customer_type) VALUES
('055-4000001', 'reg1@test.com', 'Registered'),
('055-4000002', 'reg2@test.com', 'Registered'),
('055-5000001', 'guest1@test.com', 'Unregistered');

-- ==========================================================
-- 4. FLIGHTS (4 Active Flights) 
-- ==========================================================

-- Flight 1: Big Plane (AP-B787-1), Long Route (TLV-JFK)
-- Requirement: 3 Pilots, 6 Attendants [cite: 45]
INSERT INTO Flights (flight_id, departure_date, airplane_id, source_airport, destination_airport, status, departure_time, runway_num) VALUES
('FL-101', '2026-05-01', 'AP-B787-1', 'TLV', 'JFK', 'Active', '23:00:00', 'R1');

INSERT INTO Pilots_In_Flights (pilot_id, flight_id) VALUES 
('P-001', 'FL-101'), ('P-002', 'FL-101'), ('P-003', 'FL-101'); -- All have long training
INSERT INTO Attendants_In_Flights (attendant_id, flight_id) VALUES
('FA-001', 'FL-101'), ('FA-002', 'FL-101'), ('FA-003', 'FL-101'),
('FA-004', 'FL-101'), ('FA-005', 'FL-101'), ('FA-006', 'FL-101');

-- Flight 2: Small Plane (AP-B737-2), Short Route (TLV-LHR)
-- Requirement: 2 Pilots, 3 Attendants [cite: 46]
INSERT INTO Flights (flight_id, departure_date, airplane_id, source_airport, destination_airport, status, departure_time, runway_num) VALUES
('FL-102', '2026-05-02', 'AP-B737-2', 'TLV', 'LHR', 'Active', '16:00:00', 'R3');

INSERT INTO Pilots_In_Flights (pilot_id, flight_id) VALUES 
('P-006', 'FL-102'), ('P-007', 'FL-102');
INSERT INTO Attendants_In_Flights (attendant_id, flight_id) VALUES
('FA-007', 'FL-102'), ('FA-008', 'FL-102'), ('FA-009', 'FL-102');

-- Flight 3: Big Plane (AP-A380-3), Short Route (TLV-CDG)
-- Requirement: 3 Pilots, 6 Attendants
INSERT INTO Flights (flight_id, departure_date, airplane_id, source_airport, destination_airport, status, departure_time, runway_num) VALUES
('FL-103', '2026-05-03', 'AP-A380-3', 'TLV', 'CDG', 'Active', '08:00:00', 'R2');

INSERT INTO Pilots_In_Flights (pilot_id, flight_id) VALUES 
('P-004', 'FL-103'), ('P-005', 'FL-103'), ('P-008', 'FL-103');
INSERT INTO Attendants_In_Flights (attendant_id, flight_id) VALUES
('FA-010', 'FL-103'), ('FA-011', 'FL-103'), ('FA-012', 'FL-103'),
('FA-013', 'FL-103'), ('FA-014', 'FL-103'), ('FA-015', 'FL-103');

-- Flight 4: Small Plane (AP-A320-4), Short Route (TLV-ETM)
-- Requirement: 2 Pilots, 3 Attendants
INSERT INTO Flights (flight_id, departure_date, airplane_id, source_airport, destination_airport, status, departure_time, runway_num) VALUES
('FL-104', '2026-05-04', 'AP-A320-4', 'TLV', 'ETM', 'Active', '10:00:00', 'R1');

INSERT INTO Pilots_In_Flights (pilot_id, flight_id) VALUES 
('P-009', 'FL-104'), ('P-010', 'FL-104');
INSERT INTO Attendants_In_Flights (attendant_id, flight_id) VALUES
('FA-016', 'FL-104'), ('FA-017', 'FL-104'), ('FA-018', 'FL-104');


-- ==========================================================
-- 5. ORDERS & TICKETS (4 Orders) 
-- ==========================================================

-- Order 1: Registered User 1, Flight 101, Business Class
INSERT INTO Orders (order_code, email, status, order_date, customer_type) VALUES
('ORD-001', 'reg1@test.com', 'Active', '2026-04-01', 'Registered');

INSERT INTO Flight_Tickets (order_code, flight_id, row_num, column_num, class_type, airplane_id, price) VALUES
('ORD-001', 'FL-101', 1, 1, 'Business', 'AP-B787-1', 1500.00);

-- Order 2: Registered User 2, Flight 101, Business Class
INSERT INTO Orders (order_code, email, status, order_date, customer_type) VALUES
('ORD-002', 'reg2@test.com', 'Active', '2026-04-02', 'Registered');

INSERT INTO Flight_Tickets (order_code, flight_id, row_num, column_num, class_type, airplane_id, price) VALUES
('ORD-002', 'FL-101', 1, 2, 'Business', 'AP-B787-1', 1500.00);

-- Order 3: Guest 1, Flight 102, Economy Class
INSERT INTO Orders (order_code, email, status, order_date, customer_type) VALUES
('ORD-003', 'guest1@test.com', 'Active', '2026-04-10', 'Unregistered');

INSERT INTO Flight_Tickets (order_code, flight_id, row_num, column_num, class_type, airplane_id, price) VALUES
('ORD-003', 'FL-102', 1, 1, 'Economy', 'AP-B737-2', 400.00);

-- Order 4: Guest 2, Flight 104, Economy Class
INSERT INTO Orders (order_code, email, status, order_date, customer_type) VALUES
('ORD-004', 'guest2@test.com', 'Active', '2026-04-15', 'Unregistered');

INSERT INTO Flight_Tickets (order_code, flight_id, row_num, column_num, class_type, airplane_id, price) VALUES
('ORD-004', 'FL-104', 1, 1, 'Economy', 'AP-A320-4', 150.00);

-- Flight 5: Big plane, long route, Arrived
INSERT INTO Flights VALUES
('FL-105', '2026-05-10', 'AP-F10X-6', 'TLV', 'JFK', 'Arrived', '22:00:00', 'R2');

INSERT INTO Pilots_In_Flights VALUES
('P-001','FL-105'), ('P-002','FL-105'), ('P-003','FL-105');

INSERT INTO Attendants_In_Flights VALUES
('FA-001','FL-105'), ('FA-002','FL-105'), ('FA-003','FL-105'),
('FA-004','FL-105'), ('FA-005','FL-105'), ('FA-006','FL-105');


-- Flight 6: Small plane, short route, Cancelled
INSERT INTO Flights VALUES
('FL-106', '2026-05-11', 'AP-F7X-5', 'TLV', 'ETM', 'Cancelled', '12:00:00', 'R3');

INSERT INTO Pilots_In_Flights VALUES
('P-006','FL-106'), ('P-007','FL-106');

INSERT INTO Attendants_In_Flights VALUES
('FA-007','FL-106'), ('FA-008','FL-106'), ('FA-009','FL-106');


-- Flight 7: Big plane, short route, Full Capacity
INSERT INTO Flights VALUES
('FL-107', '2026-06-01', 'AP-A380-3', 'TLV', 'CDG', 'Full Capacity', '09:00:00', 'R4');

INSERT INTO Pilots_In_Flights VALUES
('P-004','FL-107'), ('P-005','FL-107'), ('P-008','FL-107');

INSERT INTO Attendants_In_Flights VALUES
('FA-010','FL-107'), ('FA-011','FL-107'), ('FA-012','FL-107'),
('FA-013','FL-107'), ('FA-014','FL-107'), ('FA-015','FL-107');


-- Flight 8: Small plane, short route, Arrived
INSERT INTO Flights VALUES
('FL-108', '2026-06-05', 'AP-B737-2', 'TLV', 'LHR', 'Arrived', '15:00:00', 'R5');

INSERT INTO Pilots_In_Flights VALUES
('P-006','FL-108'), ('P-007','FL-108');

INSERT INTO Attendants_In_Flights VALUES
('FA-007','FL-108'), ('FA-008','FL-108'), ('FA-009','FL-108');


-- Flight 9: Big plane, long route, Active
INSERT INTO Flights VALUES
('FL-109', '2026-06-10', 'AP-B787-1', 'TLV', 'JFK', 'Active', '23:30:00', 'R1');

INSERT INTO Pilots_In_Flights VALUES
('P-001','FL-109'), ('P-002','FL-109'), ('P-003','FL-109');

INSERT INTO Attendants_In_Flights VALUES
('FA-001','FL-109'), ('FA-002','FL-109'), ('FA-003','FL-109'),
('FA-004','FL-109'), ('FA-005','FL-109'), ('FA-006','FL-109');


-- Flight 10: Small plane, short route, Arrived
INSERT INTO Flights VALUES
('FL-110', '2026-06-12', 'AP-A320-4', 'TLV', 'ETM', 'Arrived', '11:00:00', 'R2');

INSERT INTO Pilots_In_Flights VALUES
('P-009','FL-110'), ('P-010','FL-110');

INSERT INTO Attendants_In_Flights VALUES
('FA-016','FL-110'), ('FA-017','FL-110'), ('FA-018','FL-110');

INSERT INTO Orders VALUES
('ORD-005','reg1@test.com','Executed','2026-04-20','Registered'),
('ORD-006','reg2@test.com','Cancelled by customer','2026-04-22','Registered'),
('ORD-007','guest1@test.com','Cancelled by system','2026-04-25','Unregistered'),
('ORD-008','guest2@test.com','Executed','2026-04-28','Unregistered'),
('ORD-009','reg1@test.com','Active','2026-05-01','Registered'),
('ORD-010','guest1@test.com','Executed','2026-05-02','Unregistered');


-- Missing seats for AP-F10X-6
INSERT INTO Seats VALUES
(1,1,'Business','AP-F10X-6'),
(1,2,'Business','AP-F10X-6'),
(10,1,'Economy','AP-F10X-6');

-- Missing seat for AP-A380-3
INSERT INTO Seats VALUES
(1,2,'Business','AP-A380-3');

-- Missing seat for AP-A320-4
INSERT INTO Seats VALUES
(1,2,'Economy','AP-A320-4');

INSERT INTO Flight_Tickets VALUES
('ORD-005','FL-102',1,1,'Economy','AP-B737-2',420),
('ORD-006','FL-103',1,1,'Business','AP-A380-3',1800),
('ORD-007','FL-104',1,1,'Economy','AP-A320-4',150),
('ORD-008','FL-105',1,1,'Business','AP-F10X-6',2000),
('ORD-009','FL-105',1,2,'Business','AP-F10X-6',2000),
('ORD-010','FL-108',1,1,'Economy','AP-B737-2',380),

('ORD-001','FL-109',10,1,'Economy','AP-B787-1',700),
('ORD-002','FL-109',1,1,'Business','AP-B787-1',1600),
('ORD-003','FL-110',1,1,'Economy','AP-A320-4',160),
('ORD-004','FL-110',1,1,'Economy','AP-A320-4',160),

('ORD-005','FL-107',1,1,'Business','AP-A380-3',1900),
('ORD-006','FL-107',1,2,'Business','AP-A380-3',1900),
('ORD-007','FL-108',1,1,'Economy','AP-B737-2',390),
('ORD-008','FL-109',1,2,'Business','AP-B787-1',1600),
('ORD-009','FL-110',1,2,'Economy','AP-A320-4',160),
('ORD-010','FL-105',10,1,'Economy','AP-F10X-6',850);
