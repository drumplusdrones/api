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

        data = request.get_json(silent=True) or {}

        task_id = data.get("task_id")

        if not task_id:

            return jsonify({

                "success": False,

                "error": "task_id is required"

            }), 400

        # Values coming from Zapier

        enquiry_received_date = data.get("enquiry_received_date")

        wedding_date = data.get("wedding_date")

        wedding_location = data.get("wedding_location")

        wedding_message = data.get("wedding_message")

        gmail_thread_id = data.get("gmail_thread_id")

        # Build Wrike custom fields

        custom_fields = []

        if enquiry_received_date:

            custom_fields.append({

                "id": "IEAG4PFKJUANASXF",

                "value": enquiry_received_date

            })

        if wedding_date:

            custom_fields.append({

                "id": "IEAG4PFKHUANAO4E",

                "value": wedding_date

            })

        if wedding_location:

            custom_fields.append({

                "id": "IEAG4PFKJUANAO4G",

                "value": wedding_location

            })

        if wedding_message:

            custom_fields.append({

                "id": "IEAG4PFKJUANAO4Q",

                "value": wedding_message

            })

        if gmail_thread_id:

            custom_fields.append({

                "id": "IEAG4PFKJUANASQ6",

                "value": gmail_thread_id

            })

        if not custom_fields:

            return jsonify({

                "success": False,

                "error": "No custom field values were supplied"

            }), 400

        print("TASK ID:", task_id)

        print("CUSTOM FIELDS:", custom_fields)

        # Update Wrike

        response = requests.put(

            f"https://www.wrike.com/api/v4/tasks/{task_id}",

            headers={

                "Authorization": f"Bearer {access_token}",

                "Content-Type": "application/json"

            },

            json={

                "customFields": custom_fields

            }

        )

        print("WRIKE STATUS:", response.status_code)

        print("WRIKE RESPONSE:", response.text)

        try:

            wrike_response = response.json()

        except ValueError:

            wrike_response = response.text

        return jsonify({

            "success": response.ok,

            "wrike_status": response.status_code,

            "wrike_response": wrike_response

        }), 200

    except Exception as e:

        print("SERVER ERROR:", str(e))

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500
        
if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(os.environ.get("PORT", 10000))

    )
