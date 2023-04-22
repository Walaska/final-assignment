import os
import bcrypt
from dotenv import load_dotenv
import pymongo
from flask import Flask, request, jsonify
from pydantic import BaseModel

app = Flask(__name__)

load_dotenv()
client = pymongo.MongoClient(os.getenv('MONGO_DB_URI'))
db = client["users"]
collection = db["users"]

class User(BaseModel):
    username: str
    password: str

@app.route("/register", methods=["POST"])
def register_user():
    user = User(**request.json)
    if collection.find_one({"username": user.username}):
        return jsonify({"message": "Username already exists"}), 400
    
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    new_user = {"username": user.username, "password": hashed_password}
    collection.insert_one(new_user)
    return jsonify({"message": "User registered successfully"}), 201


@app.route("/login", methods=["POST"])
def login_user():
    user = User(**request.json)
    db_user = collection.find_one({"username": user.username})
    if not db_user:
        return jsonify({"message": "Invalid username or password"}), 400

    if not bcrypt.checkpw(user.password.encode('utf-8'), db_user["password"].encode('utf-8')):
        return jsonify({"message": "Invalid username or password"}), 400

    return jsonify({"message": "User logged in successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
