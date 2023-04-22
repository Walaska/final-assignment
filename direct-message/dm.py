import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify, abort
from flask_pymongo import PyMongo
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
load_dotenv()
app.config["MONGO_URI"] = os.getenv('MONGO_DB_URI')
mongo = PyMongo(app)

socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/send", methods=["POST"])
def send_message():
    sender = request.json.get("sender")
    receiver = request.json.get("receiver")
    message = request.json.get("message")

    if not mongo.db.users.find_one({"username": sender}):
        abort(404, description="Sender not found")
    if not mongo.db.users.find_one({"username": receiver}):
        abort(404, description="Receiver not found")

    message_data = {
        "sender": sender,
        "receiver": receiver,
        "message": message,
        "timestamp": datetime.now()
    }
    result = mongo.db.messages.insert_one(message_data)

    socketio.emit("new_message", message_data, room=receiver)

    return jsonify({"message": "Message sent successfully", "message_id": str(result.inserted_id)})

@app.route("/receive", methods=["POST"])
def receive_message():
    receiver = request.json.get("receiver")

    if not mongo.db.users.find_one({"username": receiver}):
        abort(404, description="Receiver not found")

    messages = mongo.db.messages.find({"receiver": receiver})

    return jsonify([{
        "sender": message["sender"],
        "receiver": message["receiver"],
        "message": message["message"],
        "timestamp": message["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    } for message in messages])

@app.route("/delete", methods=["POST"])
def delete_message():
    message_id = request.json.get("message_id")

    if not mongo.db.messages.find_one({"_id": message_id}):
        abort(404, description="Message not found")

    result = mongo.db.messages.delete_one({"_id": message_id})

    return jsonify({"message": "Message deleted successfully", "deleted_count": result.deleted_count})

@socketio.on("join")
def on_join(data):
    username = data["username"]
    join_room(username)

@socketio.on("leave")
def on_leave(data):
    username = data["username"]
    leave_room(username)

@socketio.on('new_message')
def handle_new_message(data):
    sender = data['sender']
    message = data['message']
    room = data['room']
    emit('new_message', {'sender': sender, 'message': message}, room=room)

if __name__ == "__main__":
    load_dotenv()
    socketio.run(app, host="0.0.0.0", port=8002)
