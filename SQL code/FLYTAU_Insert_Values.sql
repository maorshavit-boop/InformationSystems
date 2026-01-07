USE FLYTAU;

INSERT INTO Flight_Routes (source_airport, destination_airport, flight_duration) VALUES
('TLV', 'JFK', 660), ('JFK', 'TLV', 630),
('TLV', 'LHR', 330), ('TLV', 'ETM', 45),
('TLV', 'CDG', 290), ('TLV', 'BKK', 660), 
('TLV', 'DXB', 180), ('TLV', 'FCO', 240);

-- --- Airplanes (6 Planes as requested) ---
INSERT INTO Airplanes (airplane_id, manufacturer, purchase_date, size) VALUES
('AP-B787-1', 'Boeing', '2020-01-01', 'Big'),
('AP-B737-2', 'Boeing', '2019-05-15', 'Small'),
('AP-A380-3', 'Airbus', '2021-11-20', 'Big'),
('AP-A320-4', 'Airbus', '2018-03-10', 'Small'),
('AP-F7X-5',  'Dassault','2022-07-01', 'Small'),
('AP-F10X-6', 'Dassault','2023-01-01', 'Big');

-- --- Classes ---
INSERT IGNORE INTO Airplane_Classes (class_type, airplane_id, columns_count, rows_count) VALUES
('Business', 'AP-B787-1', 4, 5), 
('Economy', 'AP-B787-1', 9, 30),
('Economy',  'AP-B737-2', 6, 25),
('Business', 'AP-A380-3', 6, 10), 
('Economy', 'AP-A380-3', 10, 40),
('Economy',  'AP-A320-4', 6, 25),
('Economy',  'AP-F7X-5',  4, 15),
('Business', 'AP-F10X-6', 4, 5), 
('Economy', 'AP-F10X-6', 6, 20);

-- --- Seats Generation (Procedure) ---
DELIMITER $$

-- 1. מחיקה בטוחה (רק אם קיים)
DROP PROCEDURE IF EXISTS GenerateSeats$$

-- 2. יצירה מחדש
CREATE PROCEDURE GenerateSeats()
BEGIN
    DECLARE i INT; DECLARE j INT;
    -- AP-B787-1
    SET i=1; WHILE i<=5 DO SET j=1; WHILE j<=4 DO INSERT IGNORE INTO Seats VALUES(i,j,'Business','AP-B787-1'); SET j=j+1; END WHILE; SET i=i+1; END WHILE;
    SET i=1; WHILE i<=30 DO SET j=1; WHILE j<=9 DO INSERT IGNORE INTO Seats VALUES(i,j,'Economy','AP-B787-1'); SET j=j+1; END WHILE; SET i=i+1; END WHILE;
    -- AP-B737-2
    SET i=1; WHILE i<=25 DO SET j=1; WHILE j<=6 DO INSERT IGNORE INTO Seats VALUES(i,j,'Economy','AP-B737-2'); SET j=j+1; END WHILE; SET i=i+1; END WHILE;
    -- AP-A380-3
    SET i=1; WHILE i<=10 DO SET j=1; WHILE j<=6 DO INSERT IGNORE INTO Seats VALUES(i,j,'Business','AP-A380-3'); SET j=j+1; END WHILE; SET i=i+1; END WHILE;
    SET i=1; WHILE i<=40 DO SET j=1; WHILE j<=10 DO INSERT IGNORE INTO Seats VALUES(i,j,'Economy','AP-A380-3'); SET j=j+1; END WHILE; SET i=i+1; END WHILE;
    -- AP-A320-4
    SET i=1; WHILE i<=25 DO SET j=1; WHILE j<=6 DO INSERT IGNORE INTO Seats VALUES(i,j,'Economy','AP-A320-4'); SET j=j+1; END WHILE; SET i=i+1; END WHILE;
    -- AP-F7X-5
    SET i=1; WHILE i<=15 DO SET j=1; WHILE j<=4 DO INSERT IGNORE INTO Seats VALUES(i,j,'Economy','AP-F7X-5'); SET j=j+1; END WHILE; SET i=i+1; END WHILE;
    -- AP-F10X-6
    SET i=1; WHILE i<=5 DO SET j=1; WHILE j<=4 DO INSERT IGNORE INTO Seats VALUES(i,j,'Business','AP-F10X-6'); SET j=j+1; END WHILE; SET i=i+1; END WHILE;
    SET i=1; WHILE i<=20 DO SET j=1; WHILE j<=6 DO INSERT IGNORE INTO Seats VALUES(i,j,'Economy','AP-F10X-6'); SET j=j+1; END WHILE; SET i=i+1; END WHILE;
END$$

DELIMITER ;

-- 3. הרצה
CALL GenerateSeats();

-- 4. מחיקה בטוחה בסוף (התיקון כאן)
DROP PROCEDURE IF EXISTS GenerateSeats;

-- --- Managers (5) ---
INSERT INTO Managers VALUES
('M-001', 'pass1', 'Sarah', 'A', 'Connor', 'Tel Aviv', 'Azrieli', '1', '2015-01-01'),
('M-002', 'pass2', 'Tony', 'B', 'Stark', 'Herzliya', 'Pituach', '2', '2016-06-15'),
('M-003', 'pass3', 'Bruce', 'C', 'Wayne', 'Jerusalem', 'Main', '3', '2018-01-01'),
('M-004', 'pass4', 'Clark', 'D', 'Kent', 'Haifa', 'Sea', '4', '2019-01-01'),
('M-005', 'pass5', 'Diana', 'E', 'Prince', 'Eilat', 'Sun', '5', '2020-01-01');

-- --- Pilots (22) ---
INSERT INTO Pilots VALUES
('P-001', 'Maverick', 'M', 'Mitchell', 'Tel Aviv', 'A', '1', '2010-01-01', TRUE),
('P-002', 'Iceman', 'K', 'Kazansky', 'Haifa', 'B', '2', '2011-01-01', TRUE),
('P-003', 'Amelia', 'E', 'Earhart', 'Eilat', 'C', '3', '2012-01-01', TRUE),
('P-004', 'Chuck', 'Y', 'Yeager', 'Jerusalem', 'D', '4', '2013-01-01', TRUE),
('P-005', 'Sully', 'S', 'Sullenberger', 'Tel Aviv', 'E', '5', '2014-01-01', TRUE),
('P-006', 'Han', 'S', 'Solo', 'Rishon', 'F', '6', '2020-01-01', FALSE),
('P-007', 'Wedge', 'A', 'Antilles', 'Holon', 'G', '7', '2021-01-01', FALSE),
('P-008', 'Starbuck', 'T', 'Thrace', 'Bat Yam', 'H', '8', '2022-01-01', FALSE),
('P-009', 'Apollo', 'A', 'Adama', 'Rehovot', 'I', '9', '2023-01-01', FALSE),
('P-010', 'Fox', 'M', 'McCloud', 'Tel Aviv', 'J', '10', '2024-01-01', FALSE),
('P-011', 'Yotam', 'D', 'Cohen', 'Tel Aviv', 'R', '11', '2015-01-01', TRUE),
('P-012', 'Noa', 'S', 'Levi', 'Haifa', 'H', '12', '2016-05-15', TRUE),
('P-013', 'Ido', 'M', 'Mizrahi', 'Eilat', 'T', '13', '2018-02-20', FALSE),
('P-014', 'Dana', 'R', 'Peretz', 'Jerusalem', 'J', '14', '2019-11-10', FALSE),
('P-015', 'Guy', 'O', 'Azulai', 'Rishon', 'J', '15', '2010-06-30', TRUE),
('P-016', 'Roni', 'M', 'Friedman', 'Tel Aviv', 'D', '16', '2021-01-01', FALSE),
('P-017', 'Eyal', 'H', 'Golan', 'Rehovot', 'H', '17', '2014-08-14', TRUE),
('P-018', 'Tamar', 'Y', 'Katz', 'Givatayim', 'K', '18', '2017-03-22', TRUE),
('P-019', 'Omer', 'A', 'Biton', 'Tel Aviv', 'A', '19', '2020-09-09', FALSE),
('P-020', 'Shira', 'L', 'Shapira', 'Haifa', 'M', '20', '2012-12-12', TRUE),
('P-021', 'Doron', 'A', 'Sason', 'Holon', 'K', '21', '2016-04-01', TRUE),
('P-022', 'Maya', 'T', 'Dagan', 'Raanana', 'A', '22', '2019-07-20', FALSE);

-- --- Flight Attendants (45) ---
INSERT INTO Flight_Attendants VALUES
('FA-001', 'Rachel', 'G', 'Green', 'Tel Aviv', 'A', '1', '2018-01-01', TRUE),
('FA-002', 'Monica', 'G', 'Geller', 'Tel Aviv', 'B', '2', '2018-02-01', TRUE),
('FA-003', 'Phoebe', 'B', 'Buffay', 'Tel Aviv', 'C', '3', '2018-03-01', TRUE),
('FA-004', 'Joey', 'T', 'Tribbiani', 'Tel Aviv', 'D', '4', '2018-04-01', TRUE),
('FA-005', 'Chandler', 'M', 'Bing', 'Tel Aviv', 'E', '5', '2018-05-01', TRUE),
('FA-006', 'Ross', 'G', 'Geller', 'Tel Aviv', 'F', '6', '2018-06-01', TRUE),
('FA-007', 'Jerry', 'S', 'Seinfeld', 'Haifa', 'G', '7', '2019-01-01', FALSE),
('FA-008', 'Elaine', 'B', 'Benes', 'Haifa', 'H', '8', '2019-02-01', FALSE),
('FA-009', 'George', 'C', 'Costanza', 'Haifa', 'I', '9', '2019-03-01', FALSE),
('FA-010', 'Cosmo', 'K', 'Kramer', 'Haifa', 'J', '10', '2019-04-01', FALSE),
('FA-011', 'Ted', 'M', 'Mosby', 'Eilat', 'K', '11', '2020-01-01', FALSE),
('FA-012', 'Robin', 'S', 'Scherbatsky', 'Eilat', 'L', '12', '2020-02-01', FALSE),
('FA-013', 'Barney', 'S', 'Stinson', 'Eilat', 'M', '13', '2020-03-01', FALSE),
('FA-014', 'Lily', 'A', 'Aldrin', 'Eilat', 'N', '14', '2020-04-01', FALSE),
('FA-015', 'Marshall', 'E', 'Eriksen', 'Eilat', 'O', '15', '2020-05-01', FALSE),
('FA-016', 'Michael', 'S', 'Scott', 'Jerusalem', 'P', '16', '2021-01-01', FALSE),
('FA-017', 'Dwight', 'S', 'Schrute', 'Jerusalem', 'Q', '17', '2021-02-01', FALSE),
('FA-018', 'Jim', 'H', 'Halpert', 'Jerusalem', 'R', '18', '2021-03-01', FALSE),
('FA-019', 'Pam', 'B', 'Beesly', 'Jerusalem', 'S', '19', '2021-04-01', FALSE),
('FA-020', 'Ryan', 'H', 'Howard', 'Jerusalem', 'T', '20', '2021-05-01', FALSE),
('FA-021', 'Michal', 'A', 'Cohen', 'Tel Aviv', 'U', '21', '2020-01-01', TRUE),
('FA-022', 'Daniel', 'B', 'Levi', 'Ramat Gan', 'V', '22', '2021-02-01', TRUE),
('FA-023', 'Sarah', 'C', 'Avraham', 'Holon', 'W', '23', '2019-03-01', FALSE),
('FA-024', 'David', 'D', 'Yosef', 'Bat Yam', 'X', '24', '2022-04-01', FALSE),
('FA-025', 'Rachel', 'E', 'Yaakov', 'Tel Aviv', 'Y', '25', '2018-05-01', TRUE),
('FA-026', 'Moshe', 'F', 'Yitzhak', 'Haifa', 'Z', '26', '2023-01-01', FALSE),
('FA-027', 'Leah', 'G', 'Reuven', 'Jerusalem', 'AA', '27', '2020-06-01', TRUE),
('FA-028', 'Yossi', 'H', 'Shimon', 'Ashdod', 'BB', '28', '2021-07-01', FALSE),
('FA-029', 'Rivka', 'I', 'Levi', 'Netanya', 'CC', '29', '2019-08-01', TRUE),
('FA-030', 'Chaim', 'J', 'Yehuda', 'Bnei Brak', 'DD', '30', '2022-09-01', FALSE),
('FA-031', 'Esther', 'K', 'Dan', 'Petah Tikva', 'EE', '31', '2020-10-01', TRUE),
('FA-032', 'Shlomo', 'L', 'Naftali', 'Tel Aviv', 'FF', '32', '2021-11-01', TRUE),
('FA-033', 'Miriam', 'M', 'Gad', 'Ramat Gan', 'GG', '33', '2019-12-01', FALSE),
('FA-034', 'Avraham', 'N', 'Asher', 'Givatayim', 'HH', '34', '2022-01-15', FALSE),
('FA-035', 'Yael', 'O', 'Issachar', 'Herzliya', 'II', '35', '2018-02-20', TRUE),
('FA-036', 'Itzhak', 'P', 'Zevulun', 'Raanana', 'JJ', '36', '2023-03-10', FALSE),
('FA-037', 'Tamar', 'Q', 'Binyamin', 'Kfar Saba', 'KK', '37', '2020-04-05', TRUE),
('FA-038', 'Yaakov', 'R', 'Menashe', 'Hod Hasharon', 'LL', '38', '2021-05-25', FALSE),
('FA-039', 'Sara', 'S', 'Efraim', 'Rosh Haayin', 'MM', '39', '2019-06-30', TRUE),
('FA-040', 'Aharon', 'T', 'Haim', 'Elad', 'NN', '40', '2022-07-12', FALSE),
('FA-041', 'Dana', 'U', 'Zilber', 'Tel Aviv', 'OO', '41', '2021-01-01', TRUE),
('FA-042', 'Ben', 'V', 'Shahar', 'Haifa', 'PP', '42', '2022-02-02', TRUE),
('FA-043', 'Gal', 'W', 'Malka', 'Eilat', 'QQ', '43', '2023-03-03', FALSE),
('FA-044', 'Noam', 'X', 'Bar', 'Jerusalem', 'RR', '44', '2020-04-04', FALSE),
('FA-045', 'Shir', 'Y', 'Tal', 'Rishon', 'SS', '45', '2019-05-05', TRUE);

-- --- Flights (12 Flights) ---
INSERT INTO Flights VALUES
('FL-101', '2026-05-01', 'AP-B787-1', 'TLV', 'JFK', 'Active', '23:00:00', 'R1'),
('FL-102', '2026-05-02', 'AP-B737-2', 'TLV', 'LHR', 'Active', '16:00:00', 'R3'),
('FL-103', '2026-05-03', 'AP-A380-3', 'TLV', 'CDG', 'Active', '08:00:00', 'R2'),
('FL-104', '2026-05-04', 'AP-A320-4', 'TLV', 'ETM', 'Active', '10:00:00', 'R1'),
('FL-105', '2026-05-10', 'AP-F10X-6', 'TLV', 'JFK', 'Arrived', '22:00:00', 'R2'),
('FL-106', '2026-05-11', 'AP-F7X-5', 'TLV', 'ETM', 'Cancelled', '12:00:00', 'R3'),
('FL-107', '2026-06-01', 'AP-A380-3', 'TLV', 'CDG', 'Full Capacity', '09:00:00', 'R4'),
('FL-108', '2026-06-05', 'AP-B737-2', 'TLV', 'LHR', 'Arrived', '15:00:00', 'R5'),
('FL-109', '2026-06-10', 'AP-B787-1', 'TLV', 'JFK', 'Active', '23:30:00', 'R1'),
('FL-110', '2026-06-12', 'AP-A320-4', 'TLV', 'ETM', 'Arrived', '11:00:00', 'R2'),
('FL-111', '2026-06-15', 'AP-B787-1', 'TLV', 'BKK', 'Active', '14:00:00', 'R1'),
('FL-112', '2026-06-20', 'AP-B737-2', 'TLV', 'DXB', 'Active', '10:00:00', 'R2');

-- --- Crew Assignments ---
INSERT INTO Pilots_In_Flights (pilot_id, flight_id, departure_date) VALUES 
('P-001','FL-101','2026-05-01'), ('P-002','FL-101','2026-05-01'), ('P-003','FL-101','2026-05-01'),
('P-006','FL-102','2026-05-02'), ('P-007','FL-102','2026-05-02'),
('P-004','FL-103','2026-05-03'), ('P-005','FL-103','2026-05-03'), ('P-008','FL-103','2026-05-03'),
('P-009','FL-104','2026-05-04'), ('P-010','FL-104','2026-05-04'),
('P-001','FL-105','2026-05-10'), ('P-002','FL-105','2026-05-10'),
('P-006','FL-106','2026-05-11'), ('P-007','FL-106','2026-05-11'),
('P-004','FL-107','2026-06-01'), ('P-005','FL-107','2026-06-01'),
('P-006','FL-108','2026-06-05'), ('P-007','FL-108','2026-06-05'),
('P-001','FL-109','2026-06-10'), ('P-011','FL-109','2026-06-10'),
('P-009','FL-110','2026-06-12'), ('P-013','FL-110','2026-06-12'),
('P-015','FL-111','2026-06-15'), ('P-017','FL-111','2026-06-15'),
('P-021','FL-112','2026-06-20');

INSERT INTO Attendants_In_Flights (attendant_id, flight_id, departure_date) VALUES 
('FA-001','FL-101','2026-05-01'), ('FA-002','FL-101','2026-05-01'), ('FA-003','FL-101','2026-05-01'), ('FA-004','FL-101','2026-05-01'),
('FA-007','FL-102','2026-05-02'), ('FA-008','FL-102','2026-05-02'),
('FA-010','FL-103','2026-05-03'), ('FA-011','FL-103','2026-05-03'), ('FA-012','FL-103','2026-05-03'),
('FA-016','FL-104','2026-05-04'), ('FA-017','FL-104','2026-05-04'),
('FA-001','FL-105','2026-05-10'), ('FA-002','FL-105','2026-05-10'),
('FA-007','FL-106','2026-05-11'), ('FA-008','FL-106','2026-05-11'),
('FA-010','FL-107','2026-06-01'), ('FA-011','FL-107','2026-06-01'),
('FA-007','FL-108','2026-06-05'), ('FA-008','FL-108','2026-06-05'),
('FA-001','FL-109','2026-06-10'), ('FA-021','FL-109','2026-06-10'),
('FA-016','FL-110','2026-06-12'), ('FA-023','FL-110','2026-06-12'),
('FA-025','FL-111','2026-06-15'), ('FA-027','FL-111','2026-06-15'),
('FA-031','FL-112','2026-06-20');

-- --- Flight Prices (Classes_In_Flights) ---
INSERT INTO Classes_In_Flights VALUES
('FL-101', '2026-05-01', 'Business', 'AP-B787-1', 1500), ('FL-101', '2026-05-01', 'Economy', 'AP-B787-1', 800),
('FL-102', '2026-05-02', 'Economy', 'AP-B737-2', 400),
('FL-103', '2026-05-03', 'Business', 'AP-A380-3', 1800), ('FL-103', '2026-05-03', 'Economy', 'AP-A380-3', 900),
('FL-104', '2026-05-04', 'Economy', 'AP-A320-4', 150),
('FL-105', '2026-05-10', 'Business', 'AP-F10X-6', 2000), ('FL-105', '2026-05-10', 'Economy', 'AP-F10X-6', 850),
('FL-106', '2026-05-11', 'Economy', 'AP-F7X-5', 200),
('FL-107', '2026-06-01', 'Business', 'AP-A380-3', 1900), ('FL-107', '2026-06-01', 'Economy', 'AP-A380-3', 950),
('FL-108', '2026-06-05', 'Economy', 'AP-B737-2', 380),
('FL-109', '2026-06-10', 'Business', 'AP-B787-1', 1600), ('FL-109', '2026-06-10', 'Economy', 'AP-B787-1', 700),
('FL-110', '2026-06-12', 'Economy', 'AP-A320-4', 160),
('FL-111', '2026-06-15', 'Business', 'AP-B787-1', 1550), ('FL-111', '2026-06-15', 'Economy', 'AP-B787-1', 750),
('FL-112', '2026-06-20', 'Economy', 'AP-B737-2', 450);

-- --- Orders (15 Orders) ---
INSERT IGNORE INTO Orders VALUES
('ORD-001','reg1@test.com','Active','2026-04-01','Registered'), ('ORD-002','reg2@test.com','Active','2026-04-02','Registered'),
('ORD-003','guest1@test.com','Active','2026-04-10','Unregistered'), ('ORD-004','guest2@test.com','Active','2026-04-15','Unregistered'),
('ORD-005','reg1@test.com','Executed','2026-04-20','Registered'), ('ORD-006','reg2@test.com','Cancelled by customer','2026-04-22','Registered'),
('ORD-007','guest1@test.com','Cancelled by system','2026-04-25','Unregistered'), ('ORD-008','guest2@test.com','Executed','2026-04-28','Unregistered'),
('ORD-009','reg1@test.com','Active','2026-05-01','Registered'), ('ORD-010','guest1@test.com','Executed','2026-05-02','Unregistered'),
('ORD-011','guest2@test.com','Active','2026-05-15','Unregistered'), ('ORD-012','reg2@test.com','Active','2026-05-16','Registered'),
('ORD-013','guest1@test.com','Active','2026-05-17','Unregistered'), ('ORD-014','reg1@test.com','Active','2026-05-18','Registered'),
('ORD-015','reg2@test.com','Active','2026-05-19','Registered');

-- --- Tickets (Many Tickets) ---
INSERT INTO Flight_Tickets (order_code, flight_id, departure_date, row_num, column_num, class_type, airplane_id) VALUES
('ORD-001', 'FL-101', '2026-05-01', 1, 1, 'Business', 'AP-B787-1'),
('ORD-002', 'FL-101', '2026-05-01', 1, 2, 'Business', 'AP-B787-1'),
('ORD-003', 'FL-102', '2026-05-02', 1, 1, 'Economy', 'AP-B737-2'),
('ORD-004', 'FL-104', '2026-05-04', 1, 1, 'Economy', 'AP-A320-4'),
('ORD-005', 'FL-102', '2026-05-02', 2, 1, 'Economy', 'AP-B737-2'),
('ORD-006', 'FL-103', '2026-05-03', 1, 1, 'Business', 'AP-A380-3'),
('ORD-007', 'FL-104', '2026-05-04', 2, 1, 'Economy', 'AP-A320-4'),
('ORD-008', 'FL-105', '2026-05-10', 1, 1, 'Business', 'AP-F10X-6'),
('ORD-009', 'FL-105', '2026-05-10', 1, 2, 'Business', 'AP-F10X-6'),
('ORD-010', 'FL-108', '2026-06-05', 1, 1, 'Economy', 'AP-B737-2'),
('ORD-011', 'FL-109', '2026-06-10', 1, 1, 'Business', 'AP-B787-1'),
('ORD-012', 'FL-109', '2026-06-10', 1, 2, 'Business', 'AP-B787-1'),
('ORD-013', 'FL-110', '2026-06-12', 1, 1, 'Economy', 'AP-A320-4'),
('ORD-014', 'FL-111', '2026-06-15', 1, 1, 'Business', 'AP-B787-1'),
('ORD-015', 'FL-112', '2026-06-20', 1, 1, 'Economy', 'AP-B737-2');
