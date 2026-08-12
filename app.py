import os

import requests

from flask import Flask, request, jsonify, redirect

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

@app.route("/oauth/start", methods=["GET"])

def oauth_start():

    client_id = os.environ.get("WRIKE_CLIENT_ID")

    redirect_uri = os.environ.get("WRIKE_REDIRECT_URI")

    if not client_id:

        return "WRIKE_CLIENT_ID is not configured", 500

    if not redirect_uri:

        return "WRIKE_REDIRECT_URI is not configured", 500

    authorization_url = (

        "https://login.wrike.com/oauth2/authorize"

        f"?client_id={client_id}"

        "&response_type=code"

        f"&redirect_uri={redirect_uri}"

    )

    return redirect(authorization_url)

@app.route("/oauth/callback", methods=["GET"])

def oauth_callback():

    code = request.args.get("code")

    if not code:

        return "Wrike authorization failed", 400

    client_id = os.environ.get("WRIKE_CLIENT_ID")

    client_secret = os.environ.get("WRIKE_CLIENT_SECRET")

    redirect_uri = os.environ.get("WRIKE_REDIRECT_URI")

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

    # For this test we store the token temporarily

    # in the running server process.

    app.config["WRIKE_ACCESS_TOKEN"] = tokens["access_token"]

    return jsonify({

        "success": True,

        "message": "Wrike authorization successful"

    })

@app.route("/wrike-test", methods=["GET"])

def wrike_test():

    access_token = app.config.get("WRIKE_ACCESS_TOKEN")

    if not access_token:

        return "No Wrike access token. Visit /oauth/start first.", 401

    response = requests.get(

        "https://www.wrike.com/api/v4/contacts",

        headers={

            "Authorization": f"Bearer {access_token}"

        }

    )

    return jsonify({

        "status_code": response.status_code,

        "wrike_response": response.json()

    }), response.status_code

@app.route("/update-task", methods=["POST"])

def update_task():

    access_token = app.config.get("WRIKE_ACCESS_TOKEN")

    if not access_token:

        return jsonify({

            "success": False,

            "error": "Not authenticated with Wrike"

        }), 401

    data = request.json or {}

    task_id = data.get("task_id")

    custom_fields = data.get("custom_fields", [])

    if not task_id:

        return jsonify({

            "success": False,

            "error": "task_id is required"

        }), 400

    if not custom_fields:

        return jsonify({

            "success": False,

            "error": "custom_fields is required"

        }), 400

    response = requests.put(

        f"https://www.wrike.com/api/v4/tasks/{task_id}",

        headers={

            "Authorization": f"Bearer {access_token}"

        },

        json={

            "customFields": custom_fields

        }

    )

    return jsonify({

        "status_code": response.status_code,

        "wrike_response": response.json()

    }), response.status_code

@app.route("/tasks", methods=["GET"])

def get_tasks():

    access_token = app.config.get("WRIKE_ACCESS_TOKEN")

    if not access_token:

        return jsonify({

            "success": False,

            "error": "Not authenticated with Wrike"

        }), 401

    response = requests.get(

        "https://www.wrike.com/api/v4/tasks",

        headers={

            "Authorization": f"Bearer {access_token}"

        },

        params={

            "pageSize": 20

        }

    )

    return jsonify({

        "status_code": response.status_code,

        "wrike_response": response.json()

    }), response.status_code

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(os.environ.get("PORT", 10000))

    )
