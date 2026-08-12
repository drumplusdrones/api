from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])

def home():

    return "My API is running!"

@app.route("/webhook", methods=["POST"])

def webhook():

    data = request.json

    print("Webhook received:")

    print(data)

    return jsonify({

        "success": True,

        "message": "Webhook received",

        "data": data

    }), 200

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=10000)
