from flask import Flask, redirect, url_for, render_template, request, session, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# ---------------- JSON Helpers ----------------
def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as file:
            return json.load(file)
    return {}

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

# ---------------- Pet Functions ----------------
# *** START OF CRITICAL FIX: Robust initialize_pet ***
def initialize_pet(username):
    """Initializes pet stats for a new user AND patches old user data with 'name' and 'choice'."""
    pets = load_pets()
    needs_save = False

    if username not in pets:
        # 1. New User Initialization
        pets[username] = {
            "name": "Pou",
            "level": 1,
            "experience": 0,
            "health": 100,
            "stress": 0,
            "choice": 1, # Default pet visual choice
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "happy"
        }
        needs_save = True
    else:
        # 2. Patching Old Data (CRITICAL FIX for white screen)
        # Ensure 'choice' key exists
        if "choice" not in pets[username]:
            pets[username]["choice"] = 1
            needs_save = True
            
        # Ensure 'name' key exists
        if "name" not in pets[username]:
            pets[username]["name"] = "Pou"
            needs_save = True

    if needs_save:
        save_pets(pets)
        
    return pets[username]
# *** END OF CRITICAL FIX: Robust initialize_pet ***

# Place this function inside your Pet Functions section, near initialize_pet
def update_pet_name(username, new_name):
    pets = load_pets()
    if username in pets:
        pets[username]['name'] = new_name
        # --- ADDED LINE FOR CONSISTENCY ---
        pets[username]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # ------------------------------------
        save_pets(pets)
        return True
    return False

@app.route("/edit_pet_name", methods=["POST"])
def edit_pet_name():
    if "username" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401
    
    username = session["username"]
    data = request.get_json()
    new_name = data.get("new_name", "").strip()
    
    # Basic validation (name must be 1-20 characters long)
    if new_name and 1 <= len(new_name) <= 20 and update_pet_name(username, new_name):
        return jsonify({"success": True, "new_name": new_name})
    else:
        return jsonify({"success": False, "message": "Invalid name or pet not found"}), 400


def complete_task_update_pet(username, on_time=True):
    """Update pet stats when a task is completed"""
    pets = load_pets()
    if username in pets:
        pet = pets[username]
        
        # Simplified EXP and level up logic
        exp_gain = 10 if on_time else 5
        pet["experience"] += exp_gain
        pet["stress"] = max(0, pet["stress"] - 5)
        pet["health"] = min(100, pet["health"] + 5)
        
        # Check for level up after gaining exp
        while pet["experience"] >= 50:
            pet["level"] += 1
            pet["experience"] -= 50
            
        pet["status"] = "happy"
        
        pet["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_pets(pets)
    return pet

# ---------------- Pet Data Helper ----------------
def load_user_data(username):
    """Loads a single user's pet data, prioritizing pets.json for pet stats."""
    pets = load_pets()
    users = load_users()
    
    # Start with base user data (if needed, e.g., for pet_choice)
    user_data = users.get(username, {})
    
    # Get the pet stats
    pet_stats = pets.get(username, {})

    # Combine them, prioritizing pet stats for pet details
    user_data['pet'] = pet_stats 
    
    return user_data

def update_pet_stress_from_questionnaire(username, stress_score):
    pets = load_pets()
    if username in pets:
        pet = pets[username]
        
        # Update stress based on score
        pet["stress"] = stress_score
        
        if stress_score >= 75:
            pet["status"] = "sick"
            pet["health"] = max(0, pet["health"] - 20)
        elif stress_score >= 50:
            pet["status"] = "sad"
            pet["health"] = max(0, pet["health"] - 10)
        else:
            pet["status"] = "happy"
            pet["health"] = min(100, pet["health"] + 5)
            pet["experience"] += 5
            
        pet["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_pets(pets)
    return pets.get(username)

# ---------------- Routes ----------------
@app.route("/")
def index():
    # Ensure this points to your login page template name
    return render_template("login.html")

# *** START OF LOGIN ROUTE FIX ***
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    users = load_users()
    if username in users and users[username]["password"] == password:
        session["username"] = username
        initialize_pet(username) # <-- ADDED: Initializes new pet or patches old data
        return redirect(url_for("dashboard"))
    return "<h2>Invalid username or password</h2><a href='/'>Try again</a>"
# *** END OF LOGIN ROUTE FIX ***

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    username = request.form["username"]
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]
    users = load_users()
    if username in users:
        return "<h2>Username already exists!</h2><a href='/signup'>Try a different username</a>"
    if password != confirm_password:
        return "<h2>Passwords do not match!</h2><a href='/signup'>Try again</a>"
    if len(password) < 4:
        return "<h2>Password must be at least 4 characters!</h2><a href='/signup'>Try again</a>"
    
    users[username] = {"password": password}
    save_users(users)
    initialize_pet(username) # Initialize pet here too for new users
    return "<h2>Account created successfully!</h2><a href='/'>Login here</a>"

# *** START OF DASHBOARD ROUTE FIX ***
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("index"))
    
    username = session["username"]
    
    # CRITICAL FIX: Ensure pet data is complete BEFORE loading
    initialize_pet(username) 
    
    # 1. Load user data using the new helper function
    user_data = load_user_data(username)
    pet = user_data.get("pet", {})
    
    # 2. Load all tasks, then filter for the current user
    all_tasks = load_tasks()
    user_tasks = all_tasks.get(username, [])
    
    # Sort tasks to show incomplete first, then completed.
    user_tasks.sort(key=lambda t: (t.get('completed', False), t.get('created', '')))
    
    return render_template("dashboard.html", user=username, pet=pet, tasks=user_tasks)
# *** END OF DASHBOARD ROUTE FIX ***


@app.route("/save_pet", methods=["POST"])
def save_pet():
    data = request.get_json()
    pet_choice = data.get('pet_choice')
    username = session.get('username')
    
    if not username:
        return jsonify({'success': False}), 401
    
    pets = load_pets()
    if username in pets:
        pets[username]['choice'] = pet_choice
        save_pets(pets)
        return jsonify({'success': True})
        
    return jsonify({'success': False}), 400


# --- Task ID Generator Fix (Ensures unique IDs even after deletion) ---
def generate_task_id(username):
    tasks = load_tasks()
    if username not in tasks or not tasks[username]:
        return 1
    # Find the max ID among existing tasks and add 1
    max_id = max([task["id"] for task in tasks[username]] + [0])
    return max_id + 1

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
        "id": generate_task_id(username), # Use the robust generator
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
                if task["completed"]:
                    complete_task_update_pet(username, on_time=True)
                break
        save_tasks(tasks)
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/stress_check")
def stress_check():
    if "username" not in session:
        return redirect(url_for("index"))
    return render_template("stress_questionnaire.html")

@app.route("/submit_stress", methods=["POST"])
def submit_stress():
    if "username" not in session:
        return redirect(url_for("index"))
    username = session["username"]
    
    # Gather and validate form data
    try:
        q1 = int(request.form.get("q1", 3))
        q2 = int(request.form.get("q2", 3))
        q3 = int(request.form.get("q3", 3))
        q4 = int(request.form.get("q4", 3))
        q5 = int(request.form.get("q5", 3))
    except ValueError:
        return "Invalid input for stress questionnaire."

    total = q1 + q2 + q3 + q4 + q5
    
    # Calculate stress score (0-100 range)
    # Min score = 5, Max score = 25. Range is 20.
    stress_score = ((total - 5) / 20) * 100
    stress_score = max(0, min(100, int(stress_score)))
    
    pet = update_pet_stress_from_questionnaire(username, stress_score)
    
    # You need a stress_result.html template for this to work
    # Since you didn't provide it, assuming it exists:
    return render_template("stress_result.html", stress_score=stress_score, pet=pet, user=username)


# ---------------- Run App ----------------
if __name__ == "__main__":
    app.run(debug=True)