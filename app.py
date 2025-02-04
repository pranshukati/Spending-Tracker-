from flask import Flask, request, jsonify
import psycopg2
import os
from datetime import datetime, time

app = Flask(__name__)
print("Flask app initialized")

# Get the PostgreSQL connection URL from environment variables (e.g., Render Dashboard)
db_url = os.getenv("DATABASE_URL", "postgresql://root:mgpCHqzRnwUJUCDmocaS2AE9NLttoeA2@dpg-cuh3rn23esus73fk81og-a.singapore-postgres.render.com/payments_nprg")

# Connect to the PostgreSQL database
conn = psycopg2.connect(db_url)
cursor = conn.cursor()
print("Connected to PostgreSQL")

# Create the 'payments' table if it doesn't exist
def create_table():
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            amount DECIMAL(10, 2),
            date DATE,
            time TIME
        );
        """)
        conn.commit()
        print("Table 'payments' created successfully or already exists.")
    except Exception as e:
        print(f"Error creating table: {e}")
        conn.rollback()

# Call the function to create the table when the app starts
create_table()

@app.route('/add-payment', methods=['GET'])
def add_payment():
    print("Received a GET request to /add-payment")
    
    # Retrieve data from URL query parameters
    amount = request.args.get('amount')
    date = request.args.get('date')  # Expecting format: MM/DD/YYYY
    time_param = request.args.get('time')  # Expecting format: 12:18 AM

    if not all([amount, date, time_param]):
        return jsonify({"error": "Missing data"}), 400

    try:
        # Convert date to YYYY-MM-DD format
        date_formatted = datetime.strptime(date, "%m/%d/%Y").strftime("%Y-%m-%d")
        
        # Convert time to 24-hour format (HH:MM:SS)
        time_formatted = datetime.strptime(time_param, "%I:%M %p").time()
        
        # Insert data into the PostgreSQL database
        cursor.execute("INSERT INTO payments (amount, date, time) VALUES (%s, %s, %s)", 
                       (amount, date_formatted, time_formatted))
        conn.commit()
        
        return jsonify({"message": "Payment added successfully"}), 201
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/get-payments', methods=['GET'])
def get_payments():
    print("Received a GET request to /get-payments")
    cursor.execute("SELECT * FROM payments")
    payments = cursor.fetchall()

    payments_list = []
    for payment in payments:
        # Handle date conversion to string
        date_value = payment[2].strftime('%Y-%m-%d') if isinstance(payment[2], datetime) else payment[2]
        
        # Handle time conversion to 12-hour format with AM/PM
        time_value = payment[3].strftime('%I:%M %p') if isinstance(payment[3], time) else str(payment[3])
        
        payment_data = {
            "id": payment[0],
            "amount": payment[1], 
            "date": date_value,
            "time": time_value
        }
        payments_list.append(payment_data)

    return jsonify({"payments": payments_list})

if __name__ == '__main__':
    print("Running the app...")
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv("PORT", 10000)))
