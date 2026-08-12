import os
import requests

from flask import Flask, request, jsonify, redirect

app = Flask(__name__)

# -------------------------
# Basic test
# -------------------------

@app.route("/", methods=["GET"])

def home():

    return "My API is running!"

# -------------------------
# Zapier webhook
# -------------------------

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

# -------------------------
# Start Wrike OAuth
# -------------------------

@app.route("/oauth/start", methods=["GET"])

def oauth_start():

    client_id = os.environ.get("WRIKE_CLIENT_ID")

    if not client_id:

        return "WRIKE_CLIENT_ID is not configured", 500

    redirect_uri = os.environ.get("WRIKE_REDIRECT_URI")

    if not redirect_uri:

        return "WRIKE_REDIRECT_URI is not configured", 500

    authorization_url = (

        "https://login.wrike.com/oauth2/authorize"

        f"?client_id={client_id}"

        "&response_type=code"

        f"&redirect_uri={redirect_uri}"

    )

    return redirect(authorization_url)

# -------------------------
# Wrike OAuth callback
# -------------------------

@app.route("/oauth/callback", methods=["GET"])

def oauth_callback():

    code = request.args.get("code")

    if not code:

        error = request.args.get("error")

        return f"Wrike authorization failed: {error}", 400

    client_id = os.environ.get("WRIKE_CLIENT_ID")

    client_secret = os.environ.get("WRIKE_CLIENT_SECRET")

    redirect_uri = os.environ.get("WRIKE_REDIRECT_URI")

    if not client_id or not client_secret or not redirect_uri:

        return "Wrike OAuth environment variables are not configured", 500

    response = requests.post(

        "https://login.wrike.com/oauth2/token",

        data={

            "client_id": client_id,

            "client_secret": client_secret,

            "grant_type": "authorization_code",

            "code": code,

            "redirect_uri": redirect_uri

        }

    )

    if response.status_code != 200:

        return jsonify({

            "success": False,

            "wrike_response": response.json()

        }), response.status_code

    tokens = response.json()

    print("Wrike OAuth successful")

    print("Access token received")

    print("Refresh token received")

    print("Wrike host:", tokens.get("host"))

    return jsonify({

        "success": True,

        "message": "Wrike authorization successful",

        "host": tokens.get("host"),

        "expires_in": tokens.get("expires_in")

    })

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(os.environ.get("PORT", 10000))

    )
