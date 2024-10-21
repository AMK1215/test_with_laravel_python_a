import mysql.connector
import pandas as pd

def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',       # Database host
            database='gsc_shan',     # Laravel database name
            user='root',             # Database username (adjust accordingly)
            password='password123'   # Database password (adjust accordingly)
        )
        if connection.is_connected():
            return connection
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return None

def fetch_users_data(connection):
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")  # Fetch data from 'users' table
    return cursor.fetchall()

def analyze_users_data(users):
    df = pd.DataFrame(users)
    total_balance = df['balance'].sum()
    print(f"Total balance of all users: {total_balance}")

if __name__ == "__main__":
    connection = connect_to_database()
    if connection:
        users_data = fetch_users_data(connection)
        analyze_users_data(users_data)
        connection.close()
