import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from flask import Flask, request, jsonify

app = Flask(__name__)

# Option 1: Pre-trained model
# Assume a model is pre-trained from previous data (can be loaded here).
# Mock historical data for training (replace this with your real training process)
data = pd.DataFrame({
    'MemberID': [1, 2, 3, 4],
    'BetAmount': [100, 200, 150, 300],
    'GameType': [1, 2, 1, 2],
    'PayoutAmount': [50, 100, 0, 150],
    'Status': [101, 101, 101, 101],
    'Fraudulent': [0, 0, 1, 0]  # 1 = fraud, 0 = legitimate
})

# Train the model with static data
X = data[['MemberID', 'BetAmount', 'GameType', 'PayoutAmount', 'Status']]
y = data['Fraudulent']
model = RandomForestClassifier()
model.fit(X, y)

# Option 2: Handle dynamic incoming data for predictions
@app.route('/predict_fraud', methods=['POST'])
def predict_fraud():
    input_data = request.json
    transactions = input_data['Transactions']  # Extract Transactions from the input

    # Convert Laravel request data to DataFrame for predictions
    df = pd.DataFrame(transactions)

    # Ensure only relevant features are passed to the model for prediction
    features = df[['MemberID', 'BetAmount', 'GameType', 'PayoutAmount', 'Status']]

    # Predict fraud based on the dynamically incoming data
    predictions = model.predict(features)

    # Return fraud prediction in JSON format
    return jsonify({'fraudulent': predictions.tolist()})

# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
