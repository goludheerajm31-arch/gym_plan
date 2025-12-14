from flask import Flask, render_template, request, jsonify
import json
import os

from datetime import datetime

app = Flask(__name__)

# JSON file where everything is stored
DATA_FILE = "data.json"


# -----------------------------
# Helpers for loading/saving data
# -----------------------------
def empty_data():
    """Return an empty structure if no file exists yet."""
    return {
        "custom_workouts": [],
        "daily_plans": {},
        "water_intake": {}
    }


def load_data():
    """Load data from JSON, or return empty defaults."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If file is corrupted, just reset it
            return empty_data()
    return empty_data()


def save_data(data):
    """Write updated data back to the JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# -----------------------------
# Predefined workout list
# -----------------------------
COMMON_WORKOUTS = {
    "Chest": ["Push-ups", "Bench Press", "Chest Fly"],
    "Back": ["Pull-ups", "Deadlift", "Row"],
    
    "Legs": ["Squats", "Lunges", "Leg Press"],
    "Arms": ["Bicep Curls", "Tricep Dips"],
    "Shoulders": ["Shoulder Press", "Lateral Raise"]
}


# -----------------------------
# Main Dashboard
# -----------------------------
@app.route("/")
def dashboard():
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")

    today_plan = data["daily_plans"].get(today, [])
    today_water = data["water_intake"].get(today, [])

    total_water = sum(today_water)
    water_goal = 3000  # ml
    water_remaining = max(0, water_goal - total_water)

    # small summary numbers
    total_sets = sum(w.get("sets", 0) for w in today_plan)
    total_reps = sum((w.get("reps", 0) * w.get("sets", 0)) for w in today_plan)

    progress = int((total_water / water_goal) * 100) if water_goal else 0
    progress = min(progress, 100)

    return render_template(
        "dashboard.html",
        workouts=today_plan,
        total_sets=total_sets,
        total_reps=total_reps,
        total_water=total_water,
        remaining_water=water_remaining,
        water_target=water_goal,
        progress=progress
    )


# -----------------------------
# Workout Management Pages
# -----------------------------
@app.route("/add-workouts")
def add_workouts_page():
    data = load_data()
    return render_template(
        "add_workouts.html",
        common_workouts=COMMON_WORKOUTS,
        custom_workouts=data["custom_workouts"]
    )


@app.route("/api/add-custom-workout", methods=["POST"])
def add_custom_workout():
    data = load_data()
    new_workout = request.json

    # give a simple ID
    new_workout["id"] = len(data["custom_workouts"]) + 1
    data["custom_workouts"].append(new_workout)
    save_data(data)

    return jsonify({"success": True, "workout": new_workout})


@app.route("/api/add-to-plan", methods=["POST"])
def add_to_plan():
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    incoming = request.json

    if today not in data["daily_plans"]:
        data["daily_plans"][today] = []

    # assign a plan ID so items can be removed easily
    incoming["plan_id"] = len(data["daily_plans"][today]) + 1
    data["daily_plans"][today].append(incoming)
    save_data(data)

    return jsonify({"success": True})


@app.route("/api/remove-from-plan/<int:plan_id>", methods=["DELETE"])
def remove_from_plan(plan_id):
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")

    if today in data["daily_plans"]:
        data["daily_plans"][today] = [
            w for w in data["daily_plans"][today]
            if w.get("plan_id") != plan_id
        ]
        save_data(data)

    return jsonify({"success": True})


# -----------------------------
# Water Intake
# -----------------------------
@app.route("/api/log-water", methods=["POST"])
def log_water():
    data = load_data()
    amount = request.json.get("amount", 0)
    today = datetime.now().strftime("%Y-%m-%d")

    if today not in data["water_intake"]:
        data["water_intake"][today] = []

    data["water_intake"][today].append(amount)
    save_data(data)

    total = sum(data["water_intake"][today])
    remaining = max(0, 3000 - total)

    return jsonify({
        "success": True,
        "total": total,
        "remaining": remaining
    })


# -----------------------------
# Run the Application
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
