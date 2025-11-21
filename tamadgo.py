from flask import Flask, redirect, url_for, render_template, request
import json

app = Flask(__name__)

def load_users():
    with open("users.json", "r") as file:
        return json.load(file)


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


if __name__=="__main__":
    app.run(debug=True)
