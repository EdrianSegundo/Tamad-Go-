from flask import Flask, redirect, url_for, render_template, request, session
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

def load_users():
    with open("users.json", "r") as file:
        return json.load(file)


def save_users(users):
    with open("users.json", "w") as file:
        json.dump(users, file, indent=4)


def load_tasks():
    if os.path.exists("tasks.json"):
        with open("tasks.json", "r") as file:
            return json.load(file)
    return {}


def save_tasks(tasks):
    with open("tasks.json", "w") as file:
        json.dump(tasks, file, indent=4)


def load_pets():
    if os.path.exists("pets.json"):
        with open("pets.json", "r") as file:
            return json.load(file)
    return {}


def save_pets(pets):
    with open("pets.json", "w") as file:
        json.dump(pets, file, indent=4)


def initialize_pet(username):
    """Create a new pet for a user"""
    pets = load_pets()
    if username not in pets:
        pets[username] = {
            "name": "Pou",
            "level": 1,
            "experience": 0,
            "health": 100,
            "stress": 0,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "happy"
        }
        save_pets(pets)
    return pets[username]


def complete_task_update_pet(username, on_time=True):
    """Update pet stats when a task is completed"""
    pets = load_pets()
    if username in pets:
        pet = pets[username]
        
        if on_time:
            # Task completed on time: pet grows and gains experience
            pet["experience"] += 10
            pet["stress"] -= 5  # Stress reduced
            pet["health"] = min(100, pet["health"] + 5)
            
            # Level up every 50 experience points
            if pet["experience"] >= 50:
                pet["level"] += 1
                pet["experience"] = 0
            
            pet["status"] = "happy"
        else:
            # Task not completed or overdue: pet loses health and level
            pet["health"] -= 15
            pet["stress"] += 20
            
            if pet["health"] <= 0:
                pet["status"] = "dead"
            elif pet["health"] <= 30:
                pet["status"] = "sick"
            else:
                pet["status"] = "sad"
            
            # Lose a level if health is critical
            if pet["health"] <= 0 and pet["level"] > 1:
                pet["level"] -= 1
        
        pet["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_pets(pets)
    
    return pet


def update_pet_stress_from_questionnaire(username, stress_score):
    """Update pet based on user's stress level from questionnaire (0-100)"""
    pets = load_pets()
    if username in pets:
        pet = pets[username]
        
        # Update pet stress to match user's stress level
        pet["stress"] = stress_score
        
        # Update pet status based on stress level
        if stress_score >= 75:
            # Very high stress - pet gets sick
            pet["status"] = "sick"
            pet["health"] = max(0, pet["health"] - 20)
        elif stress_score >= 50:
            # High stress - pet gets sad
            pet["status"] = "sad"
            pet["health"] = max(0, pet["health"] - 10)
        elif stress_score >= 25:
            # Moderate stress - pet is okay
            pet["status"] = "happy"
            pet["health"] = min(100, pet["health"] + 5)
        else:
            # Low stress - pet is very happy
            pet["status"] = "happy"
            pet["health"] = min(100, pet["health"] + 15)
            pet["experience"] += 5
        
        pet["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_pets(pets)
    
    return pets.get(username)


@app.route("/")
def index():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    users = load_users()

    if username in users and users[username]["password"] == password:
        session["username"] = username
        return redirect(url_for("dashboard"))
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


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("index"))
    
    username = session["username"]
    
    # Initialize pet if doesn't exist
    pet = initialize_pet(username)
    
    tasks = load_tasks()
    user_tasks = tasks.get(username, [])
    
    return render_template("dashboard.html", user=username, tasks=user_tasks, pet=pet)


@app.route("/add_task", methods=["POST"])
def add_task():
    if "username" not in session:
        return redirect(url_for("index"))
    
    username = session["username"]
    task_name = request.form["task_name"]
    
    tasks = load_tasks()
    if username not in tasks:
        tasks[username] = []
    
    new_task = {
        "id": len(tasks[username]) + 1,
        "name": task_name,
        "completed": False,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    tasks[username].append(new_task)
    save_tasks(tasks)
    
    return redirect(url_for("dashboard"))


@app.route("/delete_task/<int:task_id>")
def delete_task(task_id):
    if "username" not in session:
        return redirect(url_for("index"))
    
    username = session["username"]
    tasks = load_tasks()
    
    if username in tasks:
        tasks[username] = [task for task in tasks[username] if task["id"] != task_id]
        save_tasks(tasks)
    
    return redirect(url_for("dashboard"))


@app.route("/complete_task/<int:task_id>")
def complete_task(task_id):
    if "username" not in session:
        return redirect(url_for("index"))
    
    username = session["username"]
    tasks = load_tasks()
    
    if username in tasks:
        for task in tasks[username]:
            if task["id"] == task_id:
                task["completed"] = not task["completed"]
                
                # If task is marked as completed, update pet (on time)
                if task["completed"]:
                    complete_task_update_pet(username, on_time=True)
                
                break
        save_tasks(tasks)
    
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/stress_check", methods=["GET"])
def stress_check():
    if "username" not in session:
        return redirect(url_for("index"))
    
    return render_template("stress_questionnaire.html")


@app.route("/submit_stress", methods=["POST"])
def submit_stress():
    if "username" not in session:
        return redirect(url_for("index"))
    
    username = session["username"]
    
    # Get answers from questionnaire (1-5 scale)
    q1 = int(request.form.get("q1", 3))
    q2 = int(request.form.get("q2", 3))
    q3 = int(request.form.get("q3", 3))
    q4 = int(request.form.get("q4", 3))
    q5 = int(request.form.get("q5", 3))
    
    # Calculate stress score (0-100)
    # Sum of answers (5-25) converted to 0-100
    total = q1 + q2 + q3 + q4 + q5
    stress_score = ((total - 5) / 20) * 100
    stress_score = max(0, min(100, int(stress_score)))  # Clamp between 0-100
    
    # Update pet based on stress level
    pet = update_pet_stress_from_questionnaire(username, stress_score)
    
    return render_template("stress_result.html", 
                         stress_score=stress_score, 
                         pet=pet,
                         user=username)


if __name__=="__main__":
    app.run(debug=True)
