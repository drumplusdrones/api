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

    try:
        access_token = app.config.get("WRIKE_ACCESS_TOKEN")

        if not access_token:
            return jsonify({
                "success": False,
                "error": "Not authenticated with Wrike"
            }), 401

        # Read JSON sent by Zapier
        data = request.get_json(silent=True) or {}

        # --------------------------------------------------
        # TASK ID
        # --------------------------------------------------

        task_id = data.get("task_id")

        if not task_id:
            return jsonify({
                "success": False,
                "error": "task_id is required"
            }), 400

        # --------------------------------------------------
        # STANDARD WRIKE TASK STATUS
        # --------------------------------------------------

        status = data.get("status")

        # --------------------------------------------------
        # CUSTOM FIELD VALUES FROM ZAPIER
        # --------------------------------------------------

        enquiry_received_date = data.get("enquiry_received_date")
        enquiry_destination = data.get("enquiry_destination")
        wedding_date = data.get("wedding_date")
        wedding_location = data.get("wedding_location")
        wedding_package = data.get("wedding_package")
        wedding_message = data.get("wedding_message")
        gmail_thread_id = data.get("gmail_thread_id")

        # --------------------------------------------------
        # BUILD CUSTOM FIELDS ARRAY
        # --------------------------------------------------

        custom_fields = []

        # Enquiry Received Date
        if enquiry_received_date:
            custom_fields.append({
                "id": "IEAG4PFKJUANASXF",
                "value": enquiry_received_date
            })

        # Enquiry Destination
        if enquiry_destination:
            allowed_destinations = [
                "Meta",
                "Hitched",
                "Webflow",
                "Unspecified"
            ]

            if enquiry_destination not in allowed_destinations:
                return jsonify({
                    "success": False,
                    "error": "Invalid enquiry_destination",
                    "received": enquiry_destination,
                    "allowed_values": allowed_destinations
                }), 400

            custom_fields.append({
                "id": "IEAG4PFKJUANASQZ",
                "value": enquiry_destination
            })

        # Wedding Date
        if wedding_date:
            custom_fields.append({
                "id": "IEAG4PFKHUANAO4E",
                "value": wedding_date
            })

        # Wedding Location
        if wedding_location:
            custom_fields.append({
                "id": "IEAG4PFKJUANAO4G",
                "value": wedding_location
            })

        # Wedding Package
        if wedding_package:
            allowed_packages = [
                "Wedding Solo Bagpiper",
                "Wedding Bagpiper & Drummer",
                "Wedding Mini Pipe Band",
                "To be decided…"
            ]

            if wedding_package not in allowed_packages:
                return jsonify({
                    "success": False,
                    "error": "Invalid wedding_package",
                    "received": wedding_package,
                    "allowed_values": allowed_packages
                }), 400

            custom_fields.append({
                "id": "IEAG4PFKJUANAO4I",
                "value": wedding_package
            })

        # Wedding Message
        if wedding_message:
            custom_fields.append({
                "id": "IEAG4PFKJUANAO4Q",
                "value": wedding_message
            })

        # Gmail Thread ID
        if gmail_thread_id:
            custom_fields.append({
                "id": "IEAG4PFKJUANASQ6",
                "value": gmail_thread_id
            })

        # --------------------------------------------------
        # BUILD WRIKE REQUEST
        # --------------------------------------------------

        update_data = {}

        # Standard Wrike Status
        if status:
            update_data["status"] = status

        # Custom fields
        if custom_fields:
            update_data["customFields"] = custom_fields

        if not update_data:
            return jsonify({
                "success": False,
                "error": "No fields were supplied to update"
            }), 400

        print("===================================")
        print("UPDATING WRIKE TASK")
        print("===================================")

        print("TASK ID:")
        print(task_id)

        print("STATUS:")
        print(status)

        print("CUSTOM FIELDS:")
        print(custom_fields)

        print("REQUEST SENT TO WRIKE:")
        print(update_data)

        # --------------------------------------------------
        # SEND UPDATE TO WRIKE
        # --------------------------------------------------

        response = requests.put(
            f"https://www.wrike.com/api/v4/tasks/{task_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=update_data
        )

        print("===================================")
        print("WRIKE RESPONSE")
        print("===================================")

        print("STATUS CODE:")
        print(response.status_code)

        print("RESPONSE:")
        print(response.text)

        # Try to decode Wrike response as JSON
        try:
            wrike_response = response.json()
        except ValueError:
            wrike_response = response.text

        # --------------------------------------------------
        # RETURN RESULT TO ZAPIER
        # --------------------------------------------------

        return jsonify({
            "success": response.ok,
            "wrike_status": response.status_code,
            "wrike_response": wrike_response,
            "task_id": task_id,
            "updated_status": status,
            "updated_custom_fields": custom_fields
        }), 200

    except Exception as e:

        print("===================================")
        print("SERVER ERROR")
        print("===================================")

        print(str(e))

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
        
if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(os.environ.get("PORT", 10000))

    )
