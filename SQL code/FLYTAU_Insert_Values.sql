-- ===================================================
-- 2. Data Population (Inserts)
-- ===================================================

-- --- Pilots (22 pilots) ---
INSERT INTO Pilots VALUES 
('P001', 'Yotam', 'David', 'Cohen', 'Tel Aviv', 'Rothschild', '10', '2015-01-01', TRUE),
('P002', 'Noa', 'Sarah', 'Levi', 'Haifa', 'Herzl', '22', '2016-05-15', TRUE),
('P003', 'Ido', 'Moshe', 'Mizrahi', 'Eilat', 'Hatemarim', '5', '2018-02-20', FALSE),
('P004', 'Dana', 'Ruth', 'Peretz', 'Jerusalem', 'Jaffa', '101', '2019-11-10', FALSE),
('P005', 'Guy', 'Omer', 'Azulai', 'Rishon', 'Jabotinsky', '44', '2010-06-30', TRUE),
('P006', 'Roni', 'Michal', 'Friedman', 'Tel Aviv', 'Dizengoff', '150', '2021-01-01', FALSE),
('P007', 'Eyal', 'Haim', 'Golan', 'Rehovot', 'Herzl', '12', '2014-08-14', TRUE),
('P008', 'Tamar', 'Yael', 'Katz', 'Givatayim', 'Katznelson', '3', '2017-03-22', TRUE),
('P009', 'Omer', 'Adam', 'Biton', 'Tel Aviv', 'Allenby', '99', '2020-09-09', FALSE),
('P010', 'Shira', 'Lea', 'Shapira', 'Haifa', 'Moriah', '70', '2012-12-12', TRUE),
('P011', 'Doron', 'Avi', 'Sason', 'Holon', 'Kugel', '88', '2016-04-01', TRUE),
('P012', 'Maya', 'Tali', 'Dagan', 'Raanana', 'Ahuza', '11', '2019-07-20', FALSE),
('P013', 'Alon', 'Ben', 'Barak', 'Kfar Saba', 'Weizman', '200', '2015-11-11', TRUE),
('P014', 'Neta', 'Or', 'Hadad', 'Bat Yam', 'Yoseftal', '13', '2022-02-02', FALSE),
('P015', 'Uri', 'Ziv', 'Peleg', 'Herzliya', 'Sokolov', '55', '2013-03-30', TRUE),
('P016', 'Gal', 'Ran', 'Sofer', 'Hadera', 'Hanassi', '4', '2020-10-10', FALSE),
('P017', 'Keren', 'Shir', 'Lavi', 'Netanya', 'Herzl', '9', '2018-01-25', TRUE),
('P018', 'Yair', 'Dan', 'Lapid', 'Tel Aviv', 'Bograshov', '10', '2011-06-15', TRUE),
('P019', 'Lior', 'Tal', 'Raz', 'Ramat Hasharon', 'Ussishkin', '21', '2021-05-05', FALSE),
('P020', 'Adi', 'Mor', 'Ashkenazi', 'Givatayim', 'Ben Gurion', '33', '2017-09-18', TRUE),
('P021', 'Tom', 'Cruise', 'Topgun', 'Haifa', 'Sky', '1', '2010-01-01', TRUE),
('P022', 'Maverick', 'Pete', 'Mitchell', 'Eilat', 'Desert', '2', '2015-05-05', TRUE);

INSERT INTO Pilot_Phones VALUES 
('050-1111111', 'P001'), ('052-2222222', 'P002'), ('054-3333333', 'P003'),
('050-4444444', 'P004'), ('052-5555555', 'P005'), ('050-6666666', 'P006');

-- --- Flight Attendants (45 attendants) ---
INSERT INTO Flight_Attendants VALUES
('FA01', 'Michal', 'A', 'Cohen', 'Tel Aviv', 'Bograshov', '1', '2020-01-01', TRUE),
('FA02', 'Daniel', 'B', 'Levi', 'Ramat Gan', 'Bialik', '2', '2021-02-01', TRUE),
('FA03', 'Sarah', 'C', 'Avraham', 'Holon', 'Sokolov', '3', '2019-03-01', FALSE),
('FA04', 'David', 'D', 'Yosef', 'Bat Yam', 'Balfour', '4', '2022-04-01', FALSE),
('FA05', 'Rachel', 'E', 'Yaakov', 'Tel Aviv', 'Ben Yehuda', '5', '2018-05-01', TRUE),
('FA06', 'Moshe', 'F', 'Yitzhak', 'Haifa', 'Hanassi', '6', '2023-01-01', FALSE),
('FA07', 'Leah', 'G', 'Reuven', 'Jerusalem', 'Gaza', '7', '2020-06-01', TRUE),
('FA08', 'Yossi', 'H', 'Shimon', 'Ashdod', 'Herzl', '8', '2021-07-01', FALSE),
('FA09', 'Rivka', 'I', 'Levi', 'Netanya', 'Sderot Nitza', '9', '2019-08-01', TRUE),
('FA10', 'Chaim', 'J', 'Yehuda', 'Bnei Brak', 'Rabbi Akiva', '10', '2022-09-01', FALSE),
('FA11', 'Esther', 'K', 'Dan', 'Petah Tikva', 'Baron Hirsch', '11', '2020-10-01', TRUE),
('FA12', 'Shlomo', 'L', 'Naftali', 'Tel Aviv', 'Ibn Gabirol', '12', '2021-11-01', TRUE),
('FA13', 'Miriam', 'M', 'Gad', 'Ramat Gan', 'Abba Hillel', '13', '2019-12-01', FALSE),
('FA14', 'Avraham', 'N', 'Asher', 'Givatayim', 'Weizman', '14', '2022-01-15', FALSE),
('FA15', 'Yael', 'O', 'Issachar', 'Herzliya', 'Sokolov', '15', '2018-02-20', TRUE),
('FA16', 'Itzhak', 'P', 'Zevulun', 'Raanana', 'Ahuza', '16', '2023-03-10', FALSE),
('FA17', 'Tamar', 'Q', 'Binyamin', 'Kfar Saba', 'Weizman', '17', '2020-04-05', TRUE),
('FA18', 'Yaakov', 'R', 'Menashe', 'Hod Hasharon', 'Magdiel', '18', '2021-05-25', FALSE),
('FA19', 'Sara', 'S', 'Efraim', 'Rosh Haayin', 'Shabazi', '19', '2019-06-30', TRUE),
('FA20', 'Aharon', 'T', 'Haim', 'Elad', 'Ben Zvi', '20', '2022-07-12', FALSE),
('FA21', 'Dana', 'U', 'Zilber', 'Tel Aviv', 'Dizengoff', '21', '2021-01-01', TRUE),
('FA22', 'Ben', 'V', 'Shahar', 'Haifa', 'Moriah', '22', '2022-02-02', TRUE),
('FA23', 'Gal', 'W', 'Malka', 'Eilat', 'Hatemarim', '23', '2023-03-03', FALSE),
('FA24', 'Noam', 'X', 'Bar', 'Jerusalem', 'Jaffa', '24', '2020-04-04', FALSE),
('FA25', 'Shir', 'Y', 'Tal', 'Rishon', 'Jabotinsky', '25', '2019-05-05', TRUE),
('FA26', 'Amit', 'Z', 'Mor', 'Ashkelon', 'Agnon', '26', '2021-06-06', FALSE),
('FA27', 'Efrat', 'A', 'Katz', 'Rehovot', 'Herzl', '27', '2022-07-07', TRUE),
('FA28', 'Guy', 'B', 'Perez', 'Bat Yam', 'Balfour', '28', '2023-08-08', FALSE),
('FA29', 'Hila', 'C', 'Segal', 'Holon', 'Sokolov', '29', '2020-09-09', TRUE),
('FA30', 'Idan', 'D', 'Golan', 'Givatayim', 'Katznelson', '30', '2021-10-10', FALSE),
('FA31', 'Kobi', 'E', 'Oz', 'Sderot', 'Begin', '31', '2019-11-11', TRUE),
('FA32', 'Liat', 'F', 'Harari', 'Modiin', 'Emek', '32', '2022-12-12', TRUE),
('FA33', 'Moti', 'G', 'Lugasi', 'Netivot', 'Shalom', '33', '2023-01-13', FALSE),
('FA34', 'Nir', 'H', 'Biton', 'Afula', 'Arlosoroff', '34', '2020-02-14', FALSE),
('FA35', 'Orly', 'I', 'Weinstein', 'Kiryat Ono', 'Levi Eshkol', '35', '2021-03-15', TRUE),
('FA36', 'Pina', 'J', 'Bausch', 'Tel Aviv', 'Rothschild', '36', '2018-04-16', TRUE),
('FA37', 'Quentin', 'K', 'Tarantino', 'Ramat Aviv', 'Einstein', '37', '2022-05-17', TRUE),
('FA38', 'Rina', 'L', 'Matzliach', 'Beer Sheva', 'Rager', '38', '2023-06-18', FALSE),
('FA39', 'Sigal', 'M', 'Shachmon', 'Herzliya', 'Pituach', '39', '2020-07-19', TRUE),
('FA40', 'Tomer', 'N', 'Kapon', 'Tel Aviv', 'Florentin', '40', '2021-08-20', FALSE),
('FA41', 'Uri', 'O', 'Geller', 'Jaffa', 'Kedumim', '41', '2019-09-21', TRUE),
('FA42', 'Vered', 'P', 'Feldman', 'Givataim', 'Weizman', '42', '2022-10-22', TRUE),
('FA43', 'Yoni', 'Q', 'Rechter', 'Tel Aviv', 'Bazel', '43', '2023-11-23', FALSE),
('FA44', 'Ziv', 'R', 'Koren', 'Ramat Gan', 'Abba Hillel', '44', '2020-12-24', FALSE),
('FA45', 'Adam', 'S', 'Sandler', 'Netanya', 'Poleg', '45', '2021-01-25', TRUE);

INSERT INTO Attendant_Phones VALUES 
('050-1234567', 'FA01'), ('050-2345678', 'FA02'), ('050-3456789', 'FA03');

-- --- Managers (5 managers) ---
INSERT INTO Managers VALUES
('M001', 'pass123', 'Boss', 'The', 'Manager', 'Tel Aviv', 'Azrieli', '1', '2010-01-01'),
('M002', 'admin456', 'Big', 'Chief', 'Officer', 'Herzliya', 'Pituach', '2', '2012-02-02'),
('M003', 'secure789', 'Head', 'Of', 'Ops', 'Jerusalem', 'Knesset', '3', '2015-05-05'),
('M004', 'super321', 'Super', 'Visor', 'Hero', 'Haifa', 'Technion', '4', '2018-08-08'),
('M005', 'master654', 'Master', 'Of', 'Puppets', 'Eilat', 'Hotel', '5', '2020-10-10');

INSERT INTO Manager_Phones VALUES 
('050-9999999', 'M001'), ('052-8888888', 'M002');

-- --- Routes ---
INSERT INTO Flight_Routes VALUES
('TLV', 'JFK', 660), 
('JFK', 'TLV', 600),
('TLV', 'LHR', 300),
('LHR', 'TLV', 290),
('TLV', 'CDG', 290),
('CDG', 'TLV', 280),
('TLV', 'ETM', 50),
('ETM', 'TLV', 50),
('TLV', 'BKK', 660),
('BKK', 'TLV', 690),
('TLV', 'DXB', 180), 
('DXB', 'TLV', 190);

-- --- Airplanes (6 Planes: 3 Big, 3 Small) ---
INSERT INTO Airplanes VALUES
('AP-BIG-1', 'Boeing', '2018-05-01', 'Big'), 
('AP-BIG-2', 'Boeing', '2020-01-15', 'Big'), 
('AP-BIG-3', 'Airbus', '2019-11-20', 'Big'), 
('AP-SML-1', 'Airbus', '2019-08-20', 'Small'),
('AP-SML-2', 'Airbus', '2021-11-30', 'Small'),
('AP-SML-3', 'Boeing', '2018-02-14', 'Small');

-- --- Airplane Classes ---
-- BIG: Business + Economy. SMALL: Economy Only.
INSERT INTO Airplane_Classes VALUES
('Business', 'AP-BIG-1', 4, 4), -- 4 rows, 4 columns
('Economy', 'AP-BIG-1', 6, 30), -- 30 rows, 6 columns
('Business', 'AP-BIG-2', 4, 4),
('Economy', 'AP-BIG-2', 6, 30),
('Business', 'AP-BIG-3', 4, 4),
('Economy', 'AP-BIG-3', 6, 30),
('Economy', 'AP-SML-1', 6, 20), -- 20 rows, 6 columns
('Economy', 'AP-SML-2', 6, 20),
('Economy', 'AP-SML-3', 6, 20);

-- --- SEATS GENERATION (Using Procedure to loop and create all seats) ---
DELIMITER $$
CREATE PROCEDURE GenerateSeats()
BEGIN
    DECLARE i INT;
    DECLARE j INT;
    
    -- 1. BIG PLANE 1 (AP-BIG-1)
    -- Business: 4 Rows, 4 Cols
    SET i = 1; WHILE i <= 4 DO SET j = 1; WHILE j <= 4 DO INSERT INTO Seats VALUES (i, j, 'Business', 'AP-BIG-1'); SET j = j + 1; END WHILE; SET i = i + 1; END WHILE;
    -- Economy: 30 Rows, 6 Cols (Starting row 5)
    SET i = 5; WHILE i <= 34 DO SET j = 1; WHILE j <= 6 DO INSERT INTO Seats VALUES (i, j, 'Economy', 'AP-BIG-1'); SET j = j + 1; END WHILE; SET i = i + 1; END WHILE;

    -- 2. BIG PLANE 2 (AP-BIG-2)
    SET i = 1; WHILE i <= 4 DO SET j = 1; WHILE j <= 4 DO INSERT INTO Seats VALUES (i, j, 'Business', 'AP-BIG-2'); SET j = j + 1; END WHILE; SET i = i + 1; END WHILE;
    SET i = 5; WHILE i <= 34 DO SET j = 1; WHILE j <= 6 DO INSERT INTO Seats VALUES (i, j, 'Economy', 'AP-BIG-2'); SET j = j + 1; END WHILE; SET i = i + 1; END WHILE;

    -- 3. BIG PLANE 3 (AP-BIG-3)
    SET i = 1; WHILE i <= 4 DO SET j = 1; WHILE j <= 4 DO INSERT INTO Seats VALUES (i, j, 'Business', 'AP-BIG-3'); SET j = j + 1; END WHILE; SET i = i + 1; END WHILE;
    SET i = 5; WHILE i <= 34 DO SET j = 1; WHILE j <= 6 DO INSERT INTO Seats VALUES (i, j, 'Economy', 'AP-BIG-3'); SET j = j + 1; END WHILE; SET i = i + 1; END WHILE;

    -- 4. SMALL PLANE 1 (AP-SML-1) - 20 Rows Economy, 6 Cols
    SET i = 1; WHILE i <= 20 DO SET j = 1; WHILE j <= 6 DO INSERT INTO Seats VALUES (i, j, 'Economy', 'AP-SML-1'); SET j = j + 1; END WHILE; SET i = i + 1; END WHILE;

    -- 5. SMALL PLANE 2 (AP-SML-2)
    SET i = 1; WHILE i <= 20 DO SET j = 1; WHILE j <= 6 DO INSERT INTO Seats VALUES (i, j, 'Economy', 'AP-SML-2'); SET j = j + 1; END WHILE; SET i = i + 1; END WHILE;

    -- 6. SMALL PLANE 3 (AP-SML-3)
    SET i = 1; WHILE i <= 20 DO SET j = 1; WHILE j <= 6 DO INSERT INTO Seats VALUES (i, j, 'Economy', 'AP-SML-3'); SET j = j + 1; END WHILE; SET i = i + 1; END WHILE;

END$$
DELIMITER ;

-- Execute the procedure to fill seats
CALL GenerateSeats();
-- Drop procedure after use
DROP PROCEDURE GenerateSeats;


-- --- Flights (10 Flights) ---
-- Format: ID, Date, Plane, From, To, Status, Time, Runway
INSERT INTO Flights VALUES
('FL001', '2026-06-01', 'AP-BIG-1', 'TLV', 'JFK', 'Active', '08:00:00', 'R1'),
('FL002', '2026-06-02', 'AP-BIG-1', 'JFK', 'TLV', 'Active', '20:00:00', 'R4L'),
('FL003', '2026-06-01', 'AP-SML-1', 'TLV', 'ETM', 'Arrived', '07:00:00', 'R2'),
('FL004', '2026-06-01', 'AP-SML-2', 'TLV', 'LHR', 'Active', '10:00:00', 'R1'),
('FL005', '2026-06-05', 'AP-BIG-2', 'TLV', 'CDG', 'Cancelled', '14:00:00', 'R3'),
('FL006', '2026-06-10', 'AP-BIG-3', 'TLV', 'BKK', 'Active', '23:00:00', 'R1'),
('FL007', '2026-06-11', 'AP-BIG-3', 'BKK', 'TLV', 'Active', '15:00:00', 'R2'),
('FL008', '2026-06-01', 'AP-SML-3', 'TLV', 'DXB', 'Full Capacity', '09:00:00', 'R3'),
('FL009', '2026-06-01', 'AP-SML-1', 'ETM', 'TLV', 'Arrived', '09:00:00', 'R1'),
('FL010', '2026-06-15', 'AP-BIG-1', 'TLV', 'JFK', 'Active', '00:30:00', 'R1');


-- --- Classes In Flights (Pricing) ---
INSERT INTO Classes_In_Flights VALUES
-- FL001 (Big)
('FL001', '2026-06-01', 'Business', 'AP-BIG-1', 1500.00),
('FL001', '2026-06-01', 'Economy', 'AP-BIG-1', 800.00),
-- FL003 (Small)
('FL003', '2026-06-01', 'Economy', 'AP-SML-1', 100.00),
-- FL004 (Small)
('FL004', '2026-06-01', 'Economy', 'AP-SML-2', 400.00),
-- FL005 (Big - Cancelled)
('FL005', '2026-06-05', 'Business', 'AP-BIG-2', 1200.00),
('FL005', '2026-06-05', 'Economy', 'AP-BIG-2', 600.00),
-- FL006 (Big)
('FL006', '2026-06-10', 'Business', 'AP-BIG-3', 1800.00),
('FL006', '2026-06-10', 'Economy', 'AP-BIG-3', 900.00),
-- FL008 (Small)
('FL008', '2026-06-01', 'Economy', 'AP-SML-3', 250.00),
-- FL010 (Big)
('FL010', '2026-06-15', 'Business', 'AP-BIG-1', 1600.00),
('FL010', '2026-06-15', 'Economy', 'AP-BIG-1', 850.00);


-- --- Crew Assignments (Big=3P+6FA, Small=2P+3FA) ---

-- FL001 (Big)
INSERT INTO Pilots_In_Flights VALUES ('P001', 'FL001', '2026-06-01'), ('P002', 'FL001', '2026-06-01'), ('P003', 'FL001', '2026-06-01');
INSERT INTO Attendants_In_Flights VALUES ('FA01', '2026-06-01', 'FL001'), ('FA02', '2026-06-01', 'FL001'), ('FA03', '2026-06-01', 'FL001'), ('FA04', '2026-06-01', 'FL001'), ('FA05', '2026-06-01', 'FL001'), ('FA06', '2026-06-01', 'FL001');

-- FL003 (Small)
INSERT INTO Pilots_In_Flights VALUES ('P004', 'FL003', '2026-06-01'), ('P005', 'FL003', '2026-06-01');
INSERT INTO Attendants_In_Flights VALUES ('FA07', '2026-06-01', 'FL003'), ('FA08', '2026-06-01', 'FL003'), ('FA09', '2026-06-01', 'FL003');

-- FL004 (Small)
INSERT INTO Pilots_In_Flights VALUES ('P006', 'FL004', '2026-06-01'), ('P007', 'FL004', '2026-06-01');
INSERT INTO Attendants_In_Flights VALUES ('FA10', '2026-06-01', 'FL004'), ('FA11', '2026-06-01', 'FL004'), ('FA12', '2026-06-01', 'FL004');

-- FL005 (Big - Cancelled)
INSERT INTO Pilots_In_Flights VALUES ('P008', 'FL005', '2026-06-05'), ('P009', 'FL005', '2026-06-05'), ('P010', 'FL005', '2026-06-05');
INSERT INTO Attendants_In_Flights VALUES ('FA13', '2026-06-05', 'FL005'), ('FA14', '2026-06-05', 'FL005'), ('FA15', '2026-06-05', 'FL005'), ('FA16', '2026-06-05', 'FL005'), ('FA17', '2026-06-05', 'FL005'), ('FA18', '2026-06-05', 'FL005');

-- FL006 (Big)
INSERT INTO Pilots_In_Flights VALUES ('P011', 'FL006', '2026-06-10'), ('P012', 'FL006', '2026-06-10'), ('P013', 'FL006', '2026-06-10');
INSERT INTO Attendants_In_Flights VALUES ('FA19', '2026-06-10', 'FL006'), ('FA20', '2026-06-10', 'FL006'), ('FA21', '2026-06-10', 'FL006'), ('FA22', '2026-06-10', 'FL006'), ('FA23', '2026-06-10', 'FL006'), ('FA24', '2026-06-10', 'FL006');

-- --- Customers ---
INSERT INTO Registered_Customers VALUES
('dana@mail.com', 'Dana', 'D', 'Cohen', '987654321', '2024-01-01', '1990-05-05', 'dana123', 'Registered'),
('avi@mail.com', 'Avi', 'A', 'Levi', '123456789', '2024-02-01', '1985-08-08', 'avi456', 'Registered'),
('ron@mail.com', 'Ron', 'R', 'Shahar', '112233445', '2024-03-01', '1995-12-12', 'ron789', 'Registered'),
('shir@mail.com', 'Shir', 'S', 'Pele', '556677889', '2024-04-01', '1998-01-01', 'shir111', 'Registered'),
('noa@mail.com', 'Noa', 'N', 'Kirel', '102030405', '2024-05-15', '2001-04-10', 'unicorn', 'Registered');

INSERT INTO Unregistered_Customers VALUES
('guest1@mail.com', 'Guest', 'G', 'One', 'Unregistered'),
('guest2@mail.com', 'Tourist', 'T', 'Two', 'Unregistered'),
('guest3@mail.com', 'Visitor', 'V', 'Three', 'Unregistered'),
('guest4@mail.com', 'Traveler', 'T', 'Four', 'Unregistered');

INSERT INTO Customer_Phones VALUES
('050-0000001', 'dana@mail.com', 'Registered'),
('050-0000002', 'avi@mail.com', 'Registered'),
('054-9999999', 'guest1@mail.com', 'Unregistered');

-- --- Orders & Tickets ---
INSERT INTO Orders VALUES
('ORD-1001', 'dana@mail.com', 'Active', '2026-05-01', 'Registered'),
('ORD-1002', 'avi@mail.com', 'Active', '2026-05-02', 'Registered'),
('ORD-1003', 'guest1@mail.com', 'Executed', '2026-04-01', 'Unregistered'),
('ORD-1004', 'shir@mail.com', 'Active', '2026-05-10', 'Registered'),
('ORD-1005', 'guest2@mail.com', 'Active', '2026-05-20', 'Unregistered'),
('ORD-1006', 'dana@mail.com', 'Cancelled by system', '2026-04-30', 'Registered'), 
('ORD-1007', 'noa@mail.com', 'Active', '2026-05-25', 'Registered');

-- Ticket Details:
-- ORD-1001 (Dana): FL001 (Big), Business Class
-- UPDATED: Includes '2026-06-01' matching FL001
INSERT INTO Flight_Tickets VALUES
('ORD-1001', 'FL001', '2026-06-01', 1, 2, 'Business', 'AP-BIG-1'),
('ORD-1001', 'FL001', '2026-06-01', 1, 3, 'Business', 'AP-BIG-1');

-- ORD-1002 (Avi): FL001 (Big), Economy
INSERT INTO Flight_Tickets VALUES
('ORD-1002', 'FL001', '2026-06-01', 5, 1, 'Economy', 'AP-BIG-1');

-- ORD-1003 (Guest1): FL003 (Small), Economy
INSERT INTO Flight_Tickets VALUES
('ORD-1003', 'FL003', '2026-06-01', 6, 1, 'Economy', 'AP-SML-1');

-- ORD-1004 (Shir): FL004 (Small), Economy
INSERT INTO Flight_Tickets VALUES
('ORD-1004', 'FL004', '2026-06-01', 2, 2, 'Economy', 'AP-SML-2');

-- ORD-1006 (Dana - Cancelled): FL005 (Big)
INSERT INTO Flight_Tickets VALUES
('ORD-1006', 'FL005', '2026-06-05', 1, 1, 'Business', 'AP-BIG-2');

-- ORD-1007 (Noa): FL006 (Big), Business
INSERT INTO Flight_Tickets VALUES
('ORD-1007', 'FL006', '2026-06-10', 2, 3, 'Business', 'AP-BIG-3');