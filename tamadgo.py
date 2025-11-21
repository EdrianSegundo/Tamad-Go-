from flask import Flask, redirect, url_for, render_template, request
import json

app = Flask(__name__)

def load_users():
    with open("users.json", "r") as file:
        return json.load(file)


def save_users(users):
    with open("users.json", "w") as file:
        json.dump(users, file, indent=4)


@app.route("/")
def index():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    users = load_users()

    if username in users and users[username]["password"] == password:
        return render_template("home.html", user=username)
    else:
        return "<h2>Invalid username or password</h2><a href='/'>Try again</a>"


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    
    username = request.form["username"]
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]
    
    users = load_users()
    
    # Check if username already exists
    if username in users:
        return "<h2>Username already exists!</h2><a href='/signup'>Try a different username</a>"
    
    # Check if passwords match
    if password != confirm_password:
        return "<h2>Passwords do not match!</h2><a href='/signup'>Try again</a>"
    
    # Check if password is long enough
    if len(password) < 4:
        return "<h2>Password must be at least 4 characters!</h2><a href='/signup'>Try again</a>"
    
    # Add new user to the dictionary
    users[username] = {"password": password}
    save_users(users)
    
    return "<h2>Account created successfully!</h2><a href='/'>Login here</a>"


if __name__=="__main__":
    app.run(debug=True)
