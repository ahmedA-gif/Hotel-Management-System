-- Create database
CREATE DATABASE IF NOT EXISTS streamlit_db8;
USE streamlit_db8;

-- Guest table
CREATE TABLE Guest (
    guest_id INT PRIMARY KEY AUTO_INCREMENT,
    age INT CHECK (age >= 18),
    guest_Fname VARCHAR(20) NOT NULL,
    guest_Lname VARCHAR(20) NOT NULL,
    guest_Mname VARCHAR(20),
    Hno INT,
    StNo INT,
    City VARCHAR(30),
    gender CHAR(1) DEFAULT 'M' CHECK (gender IN ('M', 'F', 'O')),
    CNIC CHAR(13) UNIQUE,
    guest_email VARCHAR(255) UNIQUE
);

-- GuestPhoneNumber table
CREATE TABLE GuestPhoneNumber (
    guest_phone_id INT PRIMARY KEY AUTO_INCREMENT,
    guest_id INT,
    phone_number CHAR(11) UNIQUE,
    FOREIGN KEY (guest_id) REFERENCES Guest(guest_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- RoomType table
CREATE TABLE RoomType (
    type_id INT PRIMARY KEY AUTO_INCREMENT,
    type_name VARCHAR(50) NOT NULL,
    base_price DECIMAL(10,2) NOT NULL
);

-- Room table
CREATE TABLE Room (
    room_no INT PRIMARY KEY AUTO_INCREMENT,
    room_capacity INT NOT NULL CHECK (room_capacity > 0),
    room_status ENUM('vacant', 'occupied', 'maintenance') DEFAULT 'vacant',
    type_id INT,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (type_id) REFERENCES RoomType(type_id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Services table
CREATE TABLE Services (
    service_id INT PRIMARY KEY AUTO_INCREMENT,
    service_name VARCHAR(100) NOT NULL,
    service_price DECIMAL(10,2) NOT NULL
);

-- Reservation table
CREATE TABLE Reservation (
    reservation_id INT PRIMARY KEY AUTO_INCREMENT,
    reservation_date DATE NOT NULL,
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    guest_id INT,
    room_no INT,
    adults INT DEFAULT 1 CHECK (adults > 0),
    children INT DEFAULT 0,
    FOREIGN KEY (guest_id) REFERENCES Guest(guest_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (room_no) REFERENCES Room(room_no) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT valid_dates CHECK (check_out > check_in)
);

-- Billing table
CREATE TABLE Billing (
    billing_id INT PRIMARY KEY AUTO_INCREMENT,
    reservation_id INT UNIQUE,
    room_charges DECIMAL(10,2) DEFAULT 0,
    service_charges DECIMAL(10,2) DEFAULT 0,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    discount DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(12,2) GENERATED ALWAYS AS (room_charges + service_charges + tax_amount - discount) STORED,
    payment_status ENUM('pending', 'paid', 'refunded') DEFAULT 'pending',
    payment_date DATETIME,
    payment_method VARCHAR(20),
    FOREIGN KEY (reservation_id) REFERENCES Reservation(reservation_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- ReservationServices table
CREATE TABLE ReservationServices (
    res_service_id INT PRIMARY KEY AUTO_INCREMENT,
    reservation_id INT,
    service_id INT,
    quantity INT DEFAULT 1,
    service_date DATE,
    FOREIGN KEY (reservation_id) REFERENCES Reservation(reservation_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (service_id) REFERENCES Services(service_id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Department table
CREATE TABLE Department (
    dept_id INT PRIMARY KEY AUTO_INCREMENT,
    dept_name VARCHAR(50) NOT NULL,
    location VARCHAR(100)
);

-- Employee table
CREATE TABLE Employee (
    emp_id INT PRIMARY KEY AUTO_INCREMENT,
    emp_Fname VARCHAR(20) NOT NULL,
    emp_Lname VARCHAR(20) NOT NULL,
    hire_date DATE NOT NULL,
    salary DECIMAL(10,2) CHECK (salary > 0),
    dept_id INT,
    manager_id INT,
    FOREIGN KEY (dept_id) REFERENCES Department(dept_id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (manager_id) REFERENCES Employee(emp_id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- EmployeeContact table
CREATE TABLE EmployeeContact (
    contact_id INT PRIMARY KEY AUTO_INCREMENT,
    emp_id INT,
    phone VARCHAR(15),
    email VARCHAR(100),
    FOREIGN KEY (emp_id) REFERENCES Employee(emp_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Insert room types
INSERT INTO RoomType (type_name, base_price) VALUES 
('Standard', 100.00),
('Deluxe', 150.00),
('Suite', 250.00),
('Executive', 350.00);

-- Insert rooms
INSERT INTO Room (room_capacity, type_id) VALUES
(2, 1), (2, 1), (2, 1), (2, 1),  -- Standard rooms
(3, 2), (3, 2), (3, 2),          -- Deluxe rooms
(4, 3), (4, 3),                   -- Suites
(2, 4), (2, 4);                   -- Executive rooms

-- Insert services
INSERT INTO Services (service_name, service_price) VALUES
('Breakfast', 15.00),
('Laundry', 20.00),
('Airport Transfer', 50.00),
('Spa', 80.00),
('Room Service', 10.00);

-- Insert departments
INSERT INTO Department (dept_name, location) VALUES
('Front Desk', 'Lobby'),
('Housekeeping', 'Floor 1'),
('Management', 'Floor 3'),
('Food & Beverage', 'Basement');

-- Insert employees
INSERT INTO Employee (emp_Fname, emp_Lname, hire_date, salary, dept_id) VALUES
('John', 'Smith', '2020-01-15', 45000.00, 1),
('Sarah', 'Johnson', '2019-05-22', 38000.00, 2),
('Michael', 'Brown', '2021-03-10', 60000.00, 3),
('Emily', 'Davis', '2022-02-18', 32000.00, 4);

-- Set managers
UPDATE Employee SET manager_id = 3 WHERE emp_id IN (1, 2, 4);

-- Insert employee contacts
INSERT INTO EmployeeContact (emp_id, phone, email) VALUES
(1, '555-0101', 'john.smith@hotel.com'),
(2, '555-0102', 'sarah.johnson@hotel.com'),
(3, '555-0103', 'michael.brown@hotel.com'),
(4, '555-0104', 'emily.davis@hotel.com');

-- Insert guests
INSERT INTO Guest (guest_Fname, guest_Lname, age, gender, CNIC, guest_email, City) VALUES
('Robert', 'Wilson', 35, 'M', '1234567890123', 'robert.wilson@email.com', 'New York'),
('Lisa', 'Taylor', 28, 'F', '9876543210987', 'lisa.taylor@email.com', 'Boston'),
('David', 'Lee', 42, 'M', '4567890123456', 'david.lee@email.com', 'Chicago');

-- Insert guest phones
INSERT INTO GuestPhoneNumber (guest_id, phone_number) VALUES
(1, '5550201'),
(1, '5550202'),
(2, '5550301'),
(3, '5550401');

-- Insert reservations
INSERT INTO Reservation (reservation_date, check_in, check_out, guest_id, room_no, adults, children) VALUES
('2025-06-20', '2025-06-26', '2025-06-28', 1, 1, 2, 0);  -- Current date is 2025-06-26, so this is active

-- Insert reservation services
INSERT INTO ReservationServices (reservation_id, service_id, quantity, service_date) VALUES
(1, 1, 2, '2025-06-26'),  -- Breakfast
(1, 5, 1, '2025-06-26');  -- Room Service

-- Triggers
DELIMITER //
CREATE TRIGGER trg_create_bill
AFTER INSERT ON Reservation
FOR EACH ROW
BEGIN
    DECLARE room_price DECIMAL(10,2);
    DECLARE stay_days INT;
    
    SELECT base_price INTO room_price
    FROM RoomType rt
    JOIN Room r ON rt.type_id = r.type_id
    WHERE r.room_no = NEW.room_no;
    
    SET stay_days = DATEDIFF(NEW.check_out, NEW.check_in);
    
    INSERT INTO Billing (reservation_id, room_charges, tax_amount)
    VALUES (NEW.reservation_id, room_price * stay_days, (room_price * stay_days) * 0.1);
    
    UPDATE Room SET room_status = 'occupied', last_updated = NOW() WHERE room_no = NEW.room_no;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_update_service_charges
AFTER INSERT ON ReservationServices
FOR EACH ROW
BEGIN
    DECLARE new_service_total DECIMAL(10,2);
    
    SET new_service_total = (SELECT COALESCE(SUM(rs.quantity * s.service_price), 0)
                            FROM ReservationServices rs
                            JOIN Services s ON rs.service_id = s.service_id
                            WHERE rs.reservation_id = NEW.reservation_id);
    
    UPDATE Billing
    SET service_charges = new_service_total
    WHERE reservation_id = NEW.reservation_id;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_update_service_charges_after_delete
AFTER DELETE ON ReservationServices
FOR EACH ROW
BEGIN
    DECLARE new_service_total DECIMAL(10,2);
    
    SET new_service_total = (SELECT COALESCE(SUM(rs.quantity * s.service_price), 0)
                            FROM ReservationServices rs
                            JOIN Services s ON rs.service_id = s.service_id
                            WHERE rs.reservation_id = OLD.reservation_id);
    
    UPDATE Billing
    SET service_charges = new_service_total
    WHERE reservation_id = OLD.reservation_id;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_free_room_after_payment
AFTER UPDATE ON Billing
FOR EACH ROW
BEGIN
    IF NEW.payment_status = 'paid' AND OLD.payment_status != 'paid' THEN
        UPDATE Room r
        JOIN Reservation res ON r.room_no = res.room_no
        SET r.room_status = 'vacant', r.last_updated = NOW()
        WHERE res.reservation_id = NEW.reservation_id
        AND res.check_out <= CURDATE();
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER trg_prevent_overbooking
BEFORE INSERT ON Reservation
FOR EACH ROW
BEGIN
    DECLARE is_available INT;
    
    SELECT COUNT(*) INTO is_available
    FROM Reservation r
    WHERE r.room_no = NEW.room_no
    AND (
        (NEW.check_in BETWEEN r.check_in AND r.check_out) OR
        (NEW.check_out BETWEEN r.check_in AND r.check_out)
    );
    
    IF is_available > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Room is already booked for selected dates';
    END IF;
END //
DELIMITER ;

-- Procedures
DELIMITER //
CREATE PROCEDURE sp_check_in(
    IN p_guest_id INT,
    IN p_room_no INT,
    IN p_check_in DATE,
    IN p_check_out DATE,
    IN p_adults INT,
    IN p_children INT
)
BEGIN
    DECLARE room_status VARCHAR(20);
    
    SELECT room_status INTO room_status
    FROM Room WHERE room_no = p_room_no;
    
    IF room_status != 'vacant' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Room is not available for check-in';
    ELSE
        INSERT INTO Reservation (reservation_date, check_in, check_out, guest_id, room_no, adults, children)
        VALUES (CURDATE(), p_check_in, p_check_out, p_guest_id, p_room_no, p_adults, p_children);
        
        SELECT CONCAT('Check-in successful. Reservation ID: ', LAST_INSERT_ID()) AS message;
    END IF;
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE sp_check_out(
    IN p_reservation_id INT,
    IN p_payment_method VARCHAR(20)
)
BEGIN
    UPDATE Billing 
    SET payment_status = 'paid',
        payment_date = NOW(),
        payment_method = p_payment_method
    WHERE reservation_id = p_reservation_id;
    
    SELECT CONCAT('Check-out complete. Total paid: $', (SELECT total FROM Billing WHERE reservation_id = p_reservation_id)) AS message;
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE sp_daily_revenue_report(IN p_date DATE)
BEGIN
    SELECT 
        p_date AS report_date,
        COUNT(r.reservation_id) AS reservations,
        SUM(b.total) AS total_revenue,
        SUM(b.room_charges) AS room_revenue,
        SUM(b.service_charges) AS service_revenue
    FROM Billing b
    JOIN Reservation r ON b.reservation_id = r.reservation_id
    WHERE DATE(COALESCE(b.payment_date, CURDATE())) = p_date
    AND b.payment_status = 'paid';
END //
DELIMITER ;