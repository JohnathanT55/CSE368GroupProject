from flask import Flask, request, jsonify, render_template, session
from flask_pymongo import PyMongo
import requests
import secrets
from basemodel import get_brands, get_products_by_brand, query_product_model
from dotenv import load_dotenv
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/chat_db"
mongo = PyMongo(app)

# Baidu Cloud API Configuration
load_dotenv()
API_KEY = os.getenv("BAIDU_API_KEY")
SECRET_KEY = os.getenv("BAIDU_SECRET_KEY")

if not API_KEY or not SECRET_KEY:
    raise ValueError("API_KEY or SECRET_KEY is not set in .env file.")

def get_user_ip():
    return request.remote_addr or "unknown"

@app.route("/")
def index():
    """Initialize the session and generate or obtain the session_id based on the IP address"""
    user_ip = get_user_ip()
    user_session = mongo.db.sessions.find_one({"ip": user_ip})

    if not user_session:
        session["session_id"] = secrets.token_hex(8)
        mongo.db.sessions.insert_one({"ip": user_ip, "session_id": session["session_id"]})
    else:
        session["session_id"] = user_session["session_id"]

    return render_template("index.html")

@app.route("/send_message", methods=["POST"])
def send_message():
    """Process user messages"""
    user_ip = get_user_ip()
    user_message = request.json.get("message").strip()
    session_id = session["session_id"]

    # Handle the "back" operation
    if user_message.lower() == "back":
        store_message(user_ip, session_id, "User", user_message, "system")
        session.pop("mode", None)
        session.pop("brand", None)
        session.pop("product", None)
        reply = "Session reset. Please choose 'look for specific laptop' or 'normal issue'."
        store_message(user_ip, session_id, "Assistance", reply, "system")
        return jsonify({"reply": reply})
    
    # Save user messages to the database
    store_message(user_ip, session_id, "User", user_message, session.get("mode", "system"))

    # Determine the session mode (local or remote)
    if "mode" not in session:
        if "look for specific laptop" in user_message.lower():
            session["mode"] = "local"
            reply = "You selected 'specific laptop'. Please choose a brand: " + ", ".join(get_brands())
        elif "normal issue" in user_message.lower():
            session["mode"] = "remote"
            reply = "You selected 'normal issue'. Please describe your problem."
        else:
            reply = "Please choose 'look for specific laptop' or 'normal issue'."

        store_message(user_ip, session_id, "Assistance", reply, "system")
        return jsonify({"reply": reply})

    # Local mode logic
    if session["mode"] == "local":
        return handle_local_mode(user_message, session_id, user_ip)
    # Remote mode logic
    elif session["mode"] == "remote":
        return handle_remote_mode(user_message, session_id, user_ip)

def handle_local_mode(user_message, session_id, user_ip):
    """Handle Local mode logic"""
    if "brand" not in session:
        brands = get_brands()
        if user_message in brands:
            session["brand"] = user_message
            products = get_products_by_brand(user_message)
            reply = f"Available products for {user_message}: {', '.join(products)}"
        else:
            reply = "Please choose a valid brand from the list."
    elif "product" not in session:
        session["product"] = user_message
        reply = f"Ask a question about {user_message}."
    else:
        reply = query_product_model(session_id, session["brand"], session["product"], user_message)

    store_message(user_ip, session_id, "Assistance", reply, "local")
    return jsonify({"reply": reply})

def handle_remote_mode(user_message, session_id, user_ip):
    """Handle Remote mode logic"""
    access_token = get_access_token()
    url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/yi_34b_chat?access_token={access_token}"

    history_messages = mongo.db.messages.find(
        {"ip": user_ip, "mode": "remote"}
    )

    messages = [{"role": "user" if msg["sender"] == "User" else "assistant", "content": msg["message"]} for msg in history_messages]

    messages.append({"role": "user", "content": (
        "You are a Laptop info assistant. Please provide concise and to-the-point answers. "
        "You can use bullet points to list multiple items if necessary. "
        "Avoid including any unnecessary explanations or introductions."
    )})

    print(messages)

    payload = {"messages": messages}

    try:
        response = requests.post(url, json=payload)
        reply = response.json().get("result", "Sorry, I didn't understand that.")
    except Exception as e:
        print(f"Error calling Baidu API: {e}")
        reply = "API error. Please try again later."

    store_message(user_ip, session_id, "Assistance", reply, "remote")
    return jsonify({"reply": reply})

def store_message(user_ip, session_id, sender, message, mode):
    """Store messages in MongoDB"""
    mongo.db.messages.insert_one({
        "ip": user_ip,
        "session_id": session_id,
        "mode": mode,
        "sender": sender,
        "message": message
    })

@app.route("/get_history", methods=["GET"])
def get_history():
    """Get History"""
    user_ip = get_user_ip()
    session_id = session.get("session_id")

    history = mongo.db.messages.find({"ip": user_ip, "session_id": session_id})
    messages = [{"sender": msg["sender"], "message": msg["message"], "mode": msg["mode"]} for msg in history]
    return jsonify({"history": messages})

@app.route("/store_message", methods=["POST"])
def store_message_route():
    """Process front-end storage message requests"""
    data = request.json
    user_ip = get_user_ip()
    session_id = session.get("session_id", secrets.token_hex(8))  # Make sure have session_id

    # Call the defined store_message function
    store_message(
        user_ip=user_ip,
        session_id=session_id,
        sender=data.get("sender", "User"),
        message=data.get("message", ""),
        mode="system"
    )
    return jsonify({"status": "success", "message": "Message stored successfully"})

def get_access_token():
    """Get Baidu Cloud API access token"""
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    response = requests.post(url, params=params)
    return response.json().get("access_token")

if __name__ == "__main__":
    app.run(debug=True)
