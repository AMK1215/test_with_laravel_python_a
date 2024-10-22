import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load your historical betting data (adjust the path to your data)
data = pd.read_csv('betting_data.csv')

# Define features and target variable
X = data[['MemberID', 'BetAmount', 'GameType', 'PayoutAmount', 'Status']]  # features
y = data['Fraudulent']  # target: 1 (fraud) or 0 (legit)

# Train the Random Forest model
model = RandomForestClassifier()
model.fit(X, y)

# Define an API endpoint for fraud predictions
@app.route('/predict_fraud', methods=['POST'])
def predict_fraud():
    input_data = request.json
    transactions = input_data['Transactions']  # Extract Transactions from the input
    df = pd.DataFrame(transactions)  # Convert to DataFrame

    # Predict fraud using relevant features
    predictions = model.predict(df[['MemberID', 'BetAmount', 'GameType', 'PayoutAmount', 'Status']])

    return jsonify({'fraudulent': predictions.tolist()})

if __name__ == '__main__':
    app.run(debug=True)
