import mysql.connector
import pandas as pd

def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            database='python_a',
            user='root',
            password='delighT@#$2024team'
        )
        if connection.is_connected():
            return connection
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return None

def fetch_users_data(connection):
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")  # Fetch data from 'users' table
    users = cursor.fetchall()
    return users

def analyze_users_data(users):
    # Convert the list of users to a Pandas DataFrame
    df = pd.DataFrame(users)

    # 1. Calculate the total balance
    total_balance = df['balance'].sum()
    print(f"Total balance of all users: {total_balance}")

    # 2. Calculate the average balance
    average_balance = df['balance'].mean()
    print(f"Average balance of users: {average_balance}")

    # 3. Display the top 5 users by balance
    top_users = df[['user_name', 'balance']].sort_values(by='balance', ascending=False).head(5)
    print("Top 5 users by balance:")
    print(top_users)

    # 4. Categorize users by balance and count them
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

if __name__ == "__main__":
    connection = connect_to_database()
    if connection:
        users_data = fetch_users_data(connection)
        analyze_users_data(users_data)
        connection.close()
