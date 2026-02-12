import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import re

# Safe type casting helpers
def safe_float(val):
    try:
        return float(val) if val is not None else 0.0
    except:
        return 0.0

def safe_int(val):
    try:
        return int(val) if val is not None else 0
    except:
        return 0

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"]["port"],
        autocommit=True,
        # THIS IS THE CRITICAL FIX FOR TIDB CLOUD
        ssl_verify_cert=False, 
        use_pure=True
    )
conn = None
cursor = None
try:
    # Check if a table exists
    cursor.execute("SHOW TABLES LIKE 'Room'")
    result = cursor.fetchone()
    
    if not result:
        st.warning("Database tables not found. Initializing...")
        # Read and execute your SQL file
        with open('final.sql', 'r') as f:
            sql_commands = f.read().split(';')
            for command in sql_commands:
                if command.strip():
                    cursor.execute(command)
        st.success("Database initialized! Please refresh.")
except Exception as e:
    st.error(f"Error checking/creating tables: {e}")

# Enhanced Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #f5f7fa;
        padding: 20px;
    }
    .stButton>button {
        background-color: #2c3e50;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        border: none;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #34495e;
        transform: scale(1.05);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
    }
    .stButton>button:active {
        transform: scale(0.95);
    }
    .stButton>button:disabled {
        background-color: #95a5a6;
        cursor: not-allowed;
    }
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .title {
        color: #2c3e50;
        font-size: 2.5em;
        margin-bottom: 20px;
    }
    .subtitle {
        color: #34495e;
        font-size: 1.5em;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .loading::after {
        content: '';
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid white;
        border-radius: 50%;
        border-top-color: transparent;
        animation: spin 0.6s linear infinite;
        margin-left: 10px;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .error {
        color: #e74c3c;
        font-weight: bold;
    }
    .success {
        color: #2ecc71;
        font-weight: bold;
    }
    .stProgress > div > div > div > div {
        background-color: #2ecc71;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# App title
st.markdown('<h1 class="title">Hotel Management System</h1>', unsafe_allow_html=True)
# After your cursor = conn.cursor() line:

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Page", [
    "Dashboard",
    "Make Reservation",
    "Add Services",
    "Delete Services",  # New page added
    "Check Out",
    "Delete Reservation",
    "Reports",
    "Guest Management"
])

# Database connection
conn = get_db_connection()
cursor = conn.cursor(dictionary=True)

if page == "Dashboard":
    st.markdown('<h2 class="subtitle">Hotel Dashboard</h2>', unsafe_allow_html=True)

    # Occupancy Metrics
    cursor.execute("""
        SELECT 
            COUNT(*) AS total_rooms,
            SUM(CASE WHEN room_status = 'occupied' THEN 1 ELSE 0 END) AS occupied_rooms,
            ROUND(SUM(CASE WHEN room_status = 'occupied' THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS occupancy_rate
        FROM Room
    """)
    occupancy = cursor.fetchone()

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3>Hotel Occupancy</h3>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Rooms", safe_int(occupancy['total_rooms']))
    col2.metric("Occupied Rooms", safe_int(occupancy['occupied_rooms']))
    col3.metric("Occupancy Rate", f"{safe_float(occupancy['occupancy_rate']):.2f}%")

    # Add progress bar for occupancy rate
    occupancy_rate = safe_float(occupancy['occupancy_rate']) / 100
    st.progress(occupancy_rate)

    st.markdown('</div>', unsafe_allow_html=True)

    # Current Reservations
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3>Current Reservations</h3>', unsafe_allow_html=True)
    cursor.execute("""
        SELECT r.reservation_id, g.guest_Fname, g.guest_Lname, 
               r.room_no, r.check_in, r.check_out, b.payment_status
        FROM Reservation r
        JOIN Guest g ON r.guest_id = g.guest_id
        JOIN Billing b ON r.reservation_id = b.reservation_id
        WHERE r.check_out >= CURDATE()
        ORDER BY r.check_in
    """)
    current_reservations = pd.DataFrame(cursor.fetchall())
    if not current_reservations.empty:
        st.dataframe(current_reservations)
    else:
        st.info("No current reservations")
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "Make Reservation":
    st.markdown('<h2 class="subtitle">Make Reservation</h2>', unsafe_allow_html=True)
    
    # Fetch available guests for selection
    cursor.execute("SELECT guest_id, CONCAT(guest_Fname, ' ', guest_Lname) AS guest_name FROM Guest")
    guests = {row['guest_name']: row['guest_id'] for row in cursor.fetchall()}
    
    with st.form("reservation_form"):
        guest_name = st.selectbox("Guest", list(guests.keys()))
        
        # Fetch available rooms with their types and status
        cursor.execute("""
            SELECT r.room_no, rt.type_name, r.room_status, rt.base_price
            FROM Room r
            JOIN RoomType rt ON r.type_id = rt.type_id
            WHERE r.room_status = 'vacant'
            ORDER BY r.room_no
        """)
        rooms = cursor.fetchall()
        
        # Create a display string for each room
        room_options = [
            f"Room {room['room_no']} ({room['type_name']}) - {room['room_status'].capitalize()} - ${room['base_price']}/night"
            for room in rooms if room['room_status'] == 'vacant'
        ]
        if not room_options:
            st.error("No vacant rooms available. Please check back later or contact administration to free up rooms.")
            room_no = st.selectbox("Room", ["No rooms available"])
            disable_submit = True
        else:
            room_no = st.selectbox("Room", room_options)
            selected_room_no = int(room_no.split()[1])
            disable_submit = False
            
            adults = st.number_input("Adults", min_value=1, value=1)
            children = st.number_input("Children", min_value=0, value=0)
            check_in = st.date_input("Check-in Date", value=datetime.now())
            check_out = st.date_input("Check-out Date", value=datetime.now() + timedelta(days=1))
        
        submitted = st.form_submit_button("Reserve", disabled=disable_submit)
        
        if submitted and not disable_submit:
            if check_out <= check_in:
                st.error("Check-out date must be after check-in date.")
            else:
                try:
                    # Check if room is available for the selected dates
                    cursor.execute("""
                        SELECT COUNT(*) AS conflicts
                        FROM Reservation r
                        WHERE r.room_no = %s
                        AND (
                            (%s BETWEEN r.check_in AND r.check_out) OR
                            (%s BETWEEN r.check_in AND r.check_out) OR
                            (r.check_in BETWEEN %s AND %s)
                        )
                    """, (selected_room_no, check_in, check_out, check_in, check_out))
                    conflicts = cursor.fetchone()['conflicts']
                    
                    if conflicts > 0:
                        st.error("Room is already booked for the selected dates.")
                    else:
                        # Insert reservation (trigger will handle billing)
                        cursor.execute("""
                            INSERT INTO Reservation (reservation_date, guest_id, room_no, check_in, check_out, adults, children)
                            VALUES (CURDATE(), %s, %s, %s, %s, %s, %s)
                        """, (guests[guest_name], selected_room_no, check_in, check_out, adults, children))
                        
                        reservation_id = cursor.lastrowid
                        st.success(f"Reservation successful! Room {selected_room_no} has been booked. Reservation ID: {reservation_id}")
                        st.rerun()
                except mysql.connector.Error as e:
                    st.error(f"Database error: {e}")

elif page == "Add Services":
    st.markdown('<h2 class="subtitle">Add Services to Reservation</h2>', unsafe_allow_html=True)
    
    # Fetch active reservations
    cursor.execute("""
        SELECT r.reservation_id, g.guest_Fname, g.guest_Lname, rm.room_no, rt.type_name
        FROM Reservation r
        JOIN Guest g ON r.guest_id = g.guest_id
        JOIN Room rm ON r.room_no = rm.room_no
        JOIN RoomType rt ON rm.type_id = rt.type_id
        WHERE r.check_out >= CURDATE()
    """)
    reservations = cursor.fetchall()
    
    if not reservations:
        st.warning("No active reservations found.")
    else:
        reservation_options = {
            f"Reservation #{res['reservation_id']} - {res['guest_Fname']} {res['guest_Lname']} (Room {res['room_no']} - {res['type_name']})": res['reservation_id']
            for res in reservations
        }
        
        with st.form("add_services"):
            reservation_display = st.selectbox("Select Reservation", list(reservation_options.keys()))
            reservation_id = reservation_options[reservation_display]
            
            cursor.execute("SELECT service_id, service_name, service_price FROM Services")
            services = cursor.fetchall()
            service_options = {
                f"{service['service_name']} (${service['service_price']})": service['service_id']
                for service in services
            }
            
            if not services:
                st.warning("No services available.")
            else:
                service_display = st.selectbox("Select Service", list(service_options.keys()))
                service_id = service_options[service_display]
                
                quantity = st.number_input("Quantity", min_value=1, value=1)
                service_date = st.date_input("Service Date", value=datetime.now())
                
                submit_service = st.form_submit_button("Add Service")
                
                if submit_service:
                    try:
                        # Insert service
                        cursor.execute("""
                            INSERT INTO ReservationServices (reservation_id, service_id, quantity, service_date)
                            VALUES (%s, %s, %s, %s)
                        """, (reservation_id, service_id, quantity, service_date))
                        
                        # Manually update service charges and total in Billing
                        cursor.execute("""
                            SELECT SUM(rs.quantity * s.service_price) AS new_service_charges
                            FROM ReservationServices rs
                            JOIN Services s ON rs.service_id = s.service_id
                            WHERE rs.reservation_id = %s
                        """, (reservation_id,))
                        new_service_charges = safe_float(cursor.fetchone()['new_service_charges'] or 0)
                        
                        cursor.execute("""
                            UPDATE Billing
                            SET service_charges = %s
                            WHERE reservation_id = %s
                        """, (new_service_charges, reservation_id))
                        
                        st.success(f"Added {quantity} x {service_display.split(' (')[0]} to reservation #{reservation_id}")
                        st.rerun()
                    except mysql.connector.Error as e:
                        st.error(f"Database error: {e}")

elif page == "Delete Services":
    st.markdown('<h2 class="subtitle">Delete Services from Reservation</h2>', unsafe_allow_html=True)
    
    # Fetch active reservations with services
    cursor.execute("""
        SELECT r.reservation_id, g.guest_Fname, g.guest_Lname, rm.room_no, rt.type_name
        FROM Reservation r
        JOIN Guest g ON r.guest_id = g.guest_id
        JOIN Room rm ON r.room_no = rm.room_no
        JOIN RoomType rt ON rm.type_id = rt.type_id
        WHERE r.check_out >= CURDATE()
        AND EXISTS (SELECT 1 FROM ReservationServices rs WHERE rs.reservation_id = r.reservation_id)
    """)
    reservations = cursor.fetchall()
    
    if not reservations:
        st.warning("No active reservations with services found.")
    else:
        reservation_options = {
            f"Reservation #{res['reservation_id']} - {res['guest_Fname']} {res['guest_Lname']} (Room {res['room_no']} - {res['type_name']})": res['reservation_id']
            for res in reservations
        }
        
        with st.form("delete_services_form"):
            reservation_display = st.selectbox("Select Reservation", list(reservation_options.keys()))
            reservation_id = reservation_options[reservation_display]
            
            # Fetch services for the selected reservation
            cursor.execute("""
                SELECT rs.res_service_id, s.service_name, rs.quantity, rs.service_date
                FROM ReservationServices rs
                JOIN Services s ON rs.service_id = s.service_id
                WHERE rs.reservation_id = %s
            """, (reservation_id,))
            services = cursor.fetchall()
            
            if not services:
                st.warning("No services associated with this reservation.")
            else:
                service_options = {f"Service ID {service['res_service_id']} - {service['service_name']} (Qty: {service['quantity']}, Date: {service['service_date']})": service['res_service_id'] for service in services}
                service_to_delete = st.selectbox("Select Service to Delete", list(service_options.keys()))
                res_service_id = service_options[service_to_delete]
                
                submit_delete = st.form_submit_button("Delete Service")
                
                if submit_delete:
                    try:
                        # Delete the service
                        cursor.execute("DELETE FROM ReservationServices WHERE res_service_id = %s", (res_service_id,))
                        
                        # Update service charges in Billing
                        cursor.execute("""
                            SELECT SUM(rs.quantity * s.service_price) AS new_service_charges
                            FROM ReservationServices rs
                            JOIN Services s ON rs.service_id = s.service_id
                            WHERE rs.reservation_id = %s
                        """, (reservation_id,))
                        new_service_charges = safe_float(cursor.fetchone()['new_service_charges'] or 0)
                        
                        cursor.execute("""
                            UPDATE Billing
                            SET service_charges = %s
                            WHERE reservation_id = %s
                        """, (new_service_charges, reservation_id))
                        
                        st.success(f"Service with ID {res_service_id} deleted from reservation #{reservation_id}")
                        st.rerun()
                    except mysql.connector.Error as e:
                        st.error(f"Database error: {e}")

elif page == "Check Out":
    st.markdown('<h2 class="subtitle">Process Check Out</h2>', unsafe_allow_html=True)
    
    # Fetch reservations ready for checkout
    cursor.execute("""
        SELECT r.reservation_id, r.room_no, g.guest_Fname, g.guest_Lname, 
               rt.type_name, b.total AS estimated_total, b.payment_status
        FROM Reservation r
        JOIN Guest g ON r.guest_id = g.guest_id
        JOIN Room rm ON r.room_no = rm.room_no
        JOIN RoomType rt ON rm.type_id = rt.type_id
        JOIN Billing b ON r.reservation_id = b.reservation_id
        WHERE r.check_out <= CURDATE()
        AND b.payment_status = 'pending'
    """)
    checkout_reservations = cursor.fetchall()
    
    if not checkout_reservations:
        st.info("No reservations ready for checkout today.")
    else:
        reservation_options = {
            f"Reservation #{res['reservation_id']} - {res['guest_Fname']} {res['guest_Lname']} (Room {res['room_no']} - {res['type_name']}) - ${safe_float(res['estimated_total']):.2f}": res['reservation_id']
            for res in checkout_reservations
        }
        
        with st.form("checkout_form"):
            reservation_display = st.selectbox("Select Reservation to Check Out", list(reservation_options.keys()))
            reservation_id = reservation_options[reservation_display]
            
            # Get reservation details
            cursor.execute("""
                SELECT b.*, r.check_in, r.check_out, r.room_no, 
                       g.guest_Fname, g.guest_Lname, rt.type_name
                FROM Billing b
                JOIN Reservation r ON b.reservation_id = r.reservation_id
                JOIN Guest g ON r.guest_id = g.guest_id
                JOIN Room rm ON r.room_no = rm.room_no
                JOIN RoomType rt ON rm.type_id = rt.type_id
                WHERE b.reservation_id = %s
            """, (reservation_id,))
            reservation_details = cursor.fetchone()
            
            if reservation_details:
                st.markdown(f"**Guest:** {reservation_details['guest_Fname']} {reservation_details['guest_Lname']}")
                st.markdown(f"**Room:** {reservation_details['room_no']} ({reservation_details['type_name']})")
                st.markdown(f"**Stay:** {reservation_details['check_in']} to {reservation_details['check_out']}")
                
                # Display charges summary
                st.markdown("### Charges Summary")
                col1, col2, col3 = st.columns(3)
                col1.metric("Room Charges", f"${safe_float(reservation_details['room_charges']):.2f}")
                col2.metric("Service Charges", f"${safe_float(reservation_details['service_charges']):.2f}")
                col3.metric("Total Amount", f"${safe_float(reservation_details['total']):.2f}")
                
                payment_method = st.selectbox("Payment Method", ["Cash", "Credit Card", "Debit Card", "Bank Transfer"])
                
                submit_checkout = st.form_submit_button("Process Check Out")
                
                if submit_checkout:
                    try:
                        # Update payment status
                        cursor.execute("""
                            UPDATE Billing
                            SET payment_status = 'paid',
                                payment_method = %s,
                                payment_date = CURDATE()
                            WHERE reservation_id = %s
                        """, (payment_method, reservation_id))
                        
                        st.success(f"Checkout processed successfully for Room {reservation_details['room_no']}")
                        st.rerun()
                    except mysql.connector.Error as e:
                        st.error(f"Error processing checkout: {e}")

elif page == "Delete Reservation":
    st.markdown('<h2 class="subtitle">Delete Reservation</h2>', unsafe_allow_html=True)
    
    # Fetch active reservations for deletion
    cursor.execute("""
        SELECT r.reservation_id, g.guest_Fname, g.guest_Lname, 
               r.room_no, r.check_in, r.check_out, b.payment_status
        FROM Reservation r
        JOIN Guest g ON r.guest_id = g.guest_id
        JOIN Billing b ON r.reservation_id = b.reservation_id
        WHERE r.check_out >= CURDATE() AND b.payment_status = 'pending'
        ORDER BY r.check_in
    """)
    active_reservations = cursor.fetchall()
    
    if not active_reservations:
        st.info("No active reservations available for deletion.")
    else:
        reservation_options = {
            f"Reservation #{res['reservation_id']} - {res['guest_Fname']} {res['guest_Lname']} (Room {res['room_no']}, {res['check_in']} to {res['check_out']})": res['reservation_id']
            for res in active_reservations
        }
        
        with st.form("delete_reservation_form"):
            reservation_display = st.selectbox("Select Reservation to Delete", list(reservation_options.keys()))
            reservation_id = reservation_options[reservation_display]
            
            submit_delete = st.form_submit_button("Delete Reservation")
            
            if submit_delete:
                try:
                    # Check for associated services
                    cursor.execute("""
                        SELECT COUNT(*) AS service_count
                        FROM ReservationServices
                        WHERE reservation_id = %s
                    """, (reservation_id,))
                    service_count = cursor.fetchone()['service_count']
                    
                    if service_count > 0:
                        st.error("Cannot delete reservation with associated services. Use the 'Delete Services' page to remove services first.")
                    else:
                        # Delete billing and reservation records
                        cursor.execute("DELETE FROM Billing WHERE reservation_id = %s", (reservation_id,))
                        cursor.execute("DELETE FROM Reservation WHERE reservation_id = %s", (reservation_id,))
                        st.success(f"Reservation #{reservation_id} deleted successfully!")
                        st.rerun()
                except mysql.connector.Error as e:
                    st.error(f"Database error: {e}")

elif page == "Reports":
    st.markdown('<h2 class="subtitle">Reports</h2>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    # Date range selection
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start Date", value=datetime.now() - timedelta(days=7))
    end_date = col2.date_input("End Date", value=datetime.now())
    
    if start_date > end_date:
        st.error("End date must be after start date.")
    else:
        try:
            # Get all reservations in the date range
            cursor.execute("""
                SELECT 
                    r.reservation_id,
                    g.guest_Fname,
                    g.guest_Lname,
                    rm.room_no,
                    rt.type_name,
                    b.room_charges,
                    b.service_charges,
                    b.total,
                    b.payment_status,
                    b.payment_method,
                    r.check_in,
                    r.check_out
                FROM Reservation r
                JOIN Guest g ON r.guest_id = g.guest_id
                JOIN Room rm ON r.room_no = rm.room_no
                JOIN RoomType rt ON rm.type_id = rt.type_id
                JOIN Billing b ON r.reservation_id = b.reservation_id
                WHERE r.check_in BETWEEN %s AND %s
                ORDER BY r.check_in
            """, (start_date, end_date))
            
            reservations = cursor.fetchall()
            
            if reservations:
                # Create DataFrame
                report_df = pd.DataFrame(reservations)
                
                # Calculate summary metrics
                total_revenue = safe_float(report_df['total'].sum())
                total_room = safe_float(report_df['room_charges'].sum())
                total_service = safe_float(report_df['service_charges'].sum())
                paid_count = report_df[report_df['payment_status'] == 'paid'].shape[0]
                pending_count = report_df[report_df['payment_status'] == 'pending'].shape[0]
                
                # Display summary metrics
                st.markdown('<h3>Revenue Summary</h3>', unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Revenue", f"${total_revenue:.2f}")
                col2.metric("Room Revenue", f"${total_room:.2f}")
                col3.metric("Service Revenue", f"${total_service:.2f}")
                
                col1, col2 = st.columns(2)
                col1.metric("Paid Reservations", paid_count)
                col2.metric("Pending Reservations", pending_count)
                
                # Display detailed report
                st.markdown('<h3>Reservation Details</h3>', unsafe_allow_html=True)
                st.dataframe(report_df)
                
                # Export option
                csv = report_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Export to CSV",
                    csv,
                    f"hotel_report_{start_date}_to_{end_date}.csv",
                    "text/csv",
                    key='download-csv'
                )
            else:
                st.info("No reservations found for the selected period.")
        except mysql.connector.Error as err:
            st.error(f"Error generating reports: {err}")
    
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "Guest Management":
    st.markdown('<h2 class="subtitle">Manage Guests</h2>', unsafe_allow_html=True)
    
    # Display all guests
    cursor.execute("SELECT * FROM Guest ORDER BY guest_Lname, guest_Fname")
    guests = cursor.fetchall()
    
    if guests:
        guests_df = pd.DataFrame(guests)
        st.dataframe(guests_df)
    else:
        st.info("No guests found in the database.")
    
    # Add Guest Form
    with st.expander("➕ Add New Guest"):
        with st.form("add_guest"):
            col1, col2 = st.columns(2)
            fname = col1.text_input("First Name*", max_chars=20)
            lname = col2.text_input("Last Name*", max_chars=20)
            email = st.text_input("Email*")
            cnic = st.text_input("CNIC* (13 digits)", max_chars=13)
            age = st.number_input("Age*", min_value=18, max_value=100)
            gender = st.selectbox("Gender*", ["M", "F", "O"])
            city = st.text_input("City", max_chars=30)
            
            submitted = st.form_submit_button("Add Guest")
            if submitted:
                if not all([fname, lname, email, cnic]):
                    st.error("Fields marked with * are required.")
                elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                    st.error("Invalid email format.")
                elif not cnic.isdigit() or len(cnic) != 13:
                    st.error("CNIC must be 13 digits.")
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO Guest (guest_Fname, guest_Lname, guest_email, CNIC, age, gender, City)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (fname, lname, email, cnic, age, gender, city))
                        st.success("Guest added successfully!")
                        st.rerun()
                    except mysql.connector.Error as e:
                        if "Duplicate entry" in str(e):
                            st.error("A guest with this CNIC or email already exists.")
                        else:
                            st.error(f"Database error: {e}")
    
    # Update Guest Form
    with st.expander("✏️ Update Guest"):
        guest_id = st.number_input("Enter Guest ID to update", min_value=1)
        if st.button("Find Guest"):
            cursor.execute("SELECT * FROM Guest WHERE guest_id = %s", (guest_id,))
            guest = cursor.fetchone()
            
            if guest:
                st.session_state['edit_guest'] = guest
                st.success(f"Found guest: {guest['guest_Fname']} {guest['guest_Lname']}")
            else:
                st.error("Guest not found.")
                st.session_state['edit_guest'] = None
        
        if 'edit_guest' in st.session_state and st.session_state['edit_guest']:
            guest = st.session_state['edit_guest']
            with st.form("update_guest"):
                col1, col2 = st.columns(2)
                new_fname = col1.text_input("First Name", value=guest['guest_Fname'])
                new_lname = col2.text_input("Last Name", value=guest['guest_Lname'])
                new_email = st.text_input("Email", value=guest['guest_email'])
                new_cnic = st.text_input("CNIC", value=guest['CNIC'])
                new_city = st.text_input("City", value=guest.get('City', ''))
                
                submitted = st.form_submit_button("Update Guest")
                if submitted:
                    if not all([new_fname, new_lname, new_email, new_cnic]):
                        st.error("All fields are required.")
                    elif not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
                        st.error("Invalid email format.")
                    else:
                        try:
                            cursor.execute("""
                                UPDATE Guest
                                SET guest_Fname=%s, guest_Lname=%s, guest_email=%s, CNIC=%s, City=%s
                                WHERE guest_id = %s
                            """, (new_fname, new_lname, new_email, new_cnic, new_city, guest_id))
                            st.success("Guest updated successfully!")
                            st.session_state['edit_guest'] = None
                            st.rerun()
                        except mysql.connector.Error as e:
                            st.error(f"Database error: {e}")
    
    # Delete Guest
    with st.expander("🗑️ Delete Guest"):
        del_id = st.number_input("Enter Guest ID to delete", min_value=1)
        if st.button("Delete Guest"):
            try:
                # Check if guest has active reservations
                cursor.execute("""
                    SELECT COUNT(*) AS active_reservations
                    FROM Reservation
                    WHERE guest_id = %s AND check_out >= CURDATE()
                """, (del_id,))
                active_res = cursor.fetchone()['active_reservations']
                
                if active_res > 0:
                    st.error("Cannot delete guest with active reservations.")
                else:
                    cursor.execute("DELETE FROM Guest WHERE guest_id = %s", (del_id,))
                    st.success("Guest deleted successfully!")
                    st.rerun()
            except mysql.connector.Error as e:
                st.error(f"Database error: {e}")

# Close connection
cursor.close()
conn.close()
