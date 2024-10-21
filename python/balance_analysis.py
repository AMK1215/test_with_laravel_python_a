import mysql.connector
import pandas as pd

# Connect to MySQL database
def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            database='python_a',     # Your Laravel database name
            user='root',             # Replace with your MySQL username
            password='delighT@#$2024team'  # Replace with your MySQL password
        )
        if connection.is_connected():
            return connection
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return None

# Fetch users and wallets data (joined)
def fetch_users_data(connection):
    cursor = connection.cursor(dictionary=True)
    # Joining users and wallets tables to retrieve balance for each user
    cursor.execute("""
        SELECT users.id, users.user_name, users.name, users.email, users.phone, users.type, wallets.balance
        FROM users
        JOIN wallets ON users.id = wallets.holder_id
        WHERE wallets.holder_type = 'User'
    """)
    users = cursor.fetchall()
    return users

# Perform analysis on the fetched data
def analyze_users_data(users):
    # Convert the list of users to a Pandas DataFrame
    df = pd.DataFrame(users)

    # Print column names for debugging
    print("DataFrame Columns: ", df.columns)

    # Check if 'balance' column exists before proceeding
    if 'balance' in df.columns:
        # 1. Calculate the total balance of all users
        total_balance = df['balance'].sum()
        print(f"Total balance of all users: {total_balance}")

        # 2. Calculate the average balance of all users
        average_balance = df['balance'].mean()
        print(f"Average balance of users: {average_balance}")

        # 3. Display the top 5 users by balance
        top_users = df[['user_name', 'balance']].sort_values(by='balance', ascending=False).head(5)
        print("Top 5 users by balance:")
        print(top_users)

        # 4. Categorize users by balance and count the number of users in each category
        bins = [0, 1000, 10000, 100000, 1000000, float('inf')]
        labels = ['Low', 'Medium', 'High', 'Very High', 'Ultra High']
        df['balance_category'] = pd.cut(df['balance'], bins=bins, labels=labels)
        balance_category_count = df['balance_category'].value_counts()
        print("Count of users by balance category:")
        print(balance_category_count)

        # 5. Calculate the total balance per user type
        total_balance_by_type = df.groupby('type')['balance'].sum()
        print("Total balance per user type:")
        print(total_balance_by_type)
    else:
        print("Column 'balance' not found in the data.")

# Main function to execute the data fetching and analysis
if __name__ == "__main__":
    # Connect to the database
    connection = connect_to_database()
    if connection:
        # Fetch users and their balances
        users_data = fetch_users_data(connection)
        # Analyze the data
        analyze_users_data(users_data)
        # Close the database connection
        connection.close()
