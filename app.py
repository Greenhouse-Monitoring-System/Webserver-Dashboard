from flask import *
import json
import os
import time
import tomllib
import requests
import threading
from database import *
from datetime import datetime, timedelta
from collections import defaultdict
from gpt_openai import askGPT

with open("config.toml", "rb") as f:
    config = tomllib.load(f)

app = Flask(__name__)
conditions_file = config["json"]["CONDITIONS"]
currentData = config["json"]["DATA"]

container_vol = config["static"]['CONTAINER']

gms_url= config["url"]["GMS"]

gms_status = "UNKNOWN"

#load conditions from JSON file
def load_conditions():
    if os.path.exists(conditions_file):
        with open(conditions_file, 'r') as file:
            return json.load(file)
    else:
        # If user doesnt change values
        return {
            "temperature": 24.5,
            "humidity": 55.2,
            "water_level": 12.3,
            "soil_moisture": 42.3,
            "light_intensity": 400
        }

def load_currentData():
    with open(currentData, 'r') as file:
        return json.load(file)


def check_gms_status():
    try:
        response = requests.get(f"http://{gms_url}/api/ping", timeout=10)
        if response.status_code == 200:
            print("UP")
            return "UP"
    except requests.RequestException:
        pass
    print("DOWN")
    return "DOWN"

def update_gms_status():
    global gms_status
    while True:
        gms_status = check_gms_status()
        time.sleep(15)

def update_current_data():
    global currentData
    while True:
        try:
            # Request current sensor readings from the GMS API
            response = requests.get(f"http://{gms_url}/api/sensors", timeout=10)

            if response.status_code == 200:
                # Save the latest data to current-data.json
                sensor_data = response.json()
                sensor_data['distance'] = 100 - round(sensor_data['distance'] * 100 / container_vol)
                with open(currentData, 'w') as file:
                    json.dump(sensor_data, file, indent=4)
                print("Updated current-data.json with new sensor readings:", sensor_data)
            else:
                print(f"Failed to fetch sensor readings: {response.status_code}")

        except requests.RequestException as e:
            print(f"Error fetching sensor readings: {str(e)}")

        # Wait for 15 seconds before fetching again
        time.sleep(8)

@app.route("/gms_status", methods=["GET"])
def get_gms_status():
    return jsonify({"status": gms_status})

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/tips")
def tips():
    return render_template("tips.html")

@app.route("/config")
def config():
    return render_template("configuration.html")

@app.route("/simulator")
def simulator():
    return render_template("simulator.html")

@app.route("/statistics", methods=["GET", "POST"])
def statistics():
    # sets current time
    end_date = datetime.now()

    # Default timeframe if not selected
    timeframe = request.form.get("timeframe", "3months")

    # Sets start_date and interval based on selected timeframe
    if timeframe == "hour":
        start_date = end_date - timedelta(hours=1)
        interval = timedelta(minutes=10)  # Every 10 minutes
        title = "Statistics - Last Hour (Every 10 Minutes)"
        group_by = "minute"
    elif timeframe == "week":
        start_date = end_date - timedelta(weeks=1)
        interval = timedelta(days=1)  # Every day
        title = "Statistics - Last Week (Daily)"
        group_by = "day"
    else:  # Default to 3 months
        start_date = end_date - timedelta(days=90)
        interval = timedelta(weeks=1)  # Every week
        title = "Statistics - Last 3 Months (Weekly)"
        group_by = "week"

    # Fetch all sensor data from the database
    all_data = json.loads(getAll_from_db())

    # Filter data based on the selected timeframe
    filtered_data = [
        entry for entry in all_data
        if datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S") >= start_date
    ]

    # To track starting timestamp 
    first_timestamp = None

    # Group data based on selected timeframe (hour, day, week)
    grouped_data = defaultdict(list)
    for entry in filtered_data:
        timestamp = datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S")
        
        # Group by the specified timeframe (hour, day, week)
        if group_by == "minute":
            # Round the timestamp to nearest 10 minutes
            timestamp = timestamp.replace(second=0, microsecond=0)
            timestamp = timestamp - timedelta(minutes=timestamp.minute % 10)
        elif group_by == "day":
            timestamp = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # If first_timestamp is None, initializes it with the first timestamp
            if first_timestamp is None:
                first_timestamp = timestamp
        
            # Calculate the number of weeks since the first timestamp
            weeks_since_first = (timestamp - first_timestamp).days // 7
            
            # Adjust timestamp to the start of the week for each 7-day interval
            timestamp = first_timestamp + timedelta(weeks=weeks_since_first)
        
        grouped_data[timestamp].append(entry)

    # Aggregate data: Take the **latest** entry of each group
    aggregated_data = []
    for group_start, entries in grouped_data.items():
        latest_entry = max(entries, key=lambda x: datetime.strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S"))

        # Format the data with proper column names
        formatted_entry = {
            "Start Time": group_start.strftime("%Y-%m-%d %H:%M:%S"),
            "Temperature": latest_entry.get("temperature", "N/A"),
            "Humidity": latest_entry.get("humidity", "N/A"),
            "Soil Moisture": latest_entry.get("soilMoisture", "N/A"),
            "Distance": latest_entry.get("distance", "N/A"),
            "Tvoc": latest_entry.get("tvoc", "N/A"),
            "Co2": latest_entry.get("co2", "N/A"),
        }
        aggregated_data.append(formatted_entry)

    # Pass cleaned data to the template
    return render_template("statistics.html", data=aggregated_data, title=title)


@app.route("/assistant")
def assistant():
    return render_template("assistant.html")

@app.route("/askgpt", methods=["POST"])
def askgpt():
    user_question = request.json.get('question', '').strip()
    if not user_question:
        return jsonify({'error': 'Empty question'}), 400

    response = askGPT(user_question)
    print("Response from GPT:\n", response)
    return jsonify({'html': response})

@app.route("/greenhouse_home")
def greenhouse():
    conditions_data = load_currentData()
    return render_template("greenhouse.html", conditions= conditions_data)

@app.route("/greenhouse/conditions", methods=["GET", "POST"])
def display_conditions():
    conditions_data = load_conditions()
    if request.method == "POST":
        #update and save
        new_data = {
            "time" : time.time(),
            "temperature" : float(request.form["temperature"]),
            "humidity" : float(request.form["humidity"]),
            "water_level" : float(request.form["water_level"]),
            "soil_moisture" : float(request.form["soil_moisture"]),
            "light_intensity" : int(request.form["light_intensity"])
        }
        
        print("HERE ARE THE UPDATED CONDITIONS", conditions_data)

        # save updated data to JSON file
        with open(conditions_file, 'w') as file:
            json.dump(new_data, file, indent = 4)
            print("SAVED conditions to file: ", new_data)

        #reload conditions after user saves
        conditions_data = new_data
        
    #pass intance to template 
    return render_template("conditions.html", conditions= conditions_data)

@app.route("/get_current", methods=["GET"])
def get_current_conditions():
    if request.method == "GET":
        conditions_data = load_currentData()
        return jsonify({
            "conditions": conditions_data,
            "image_url": "http://127.0.0.1:8080/static/upload_imgs/current/now.jpg"  # Image hosted by Flask
        })

@app.route("/control", methods=["GET"])
def control_page():
    conditions_data = load_conditions()
    motor_state = conditions_data.get("water_pump_state", "OFF")
    fan_state = conditions_data.get("ventilation_state", "OFF")
    return render_template("control.html", motor_state=motor_state, fan_state=fan_state)

@app.route("/toggle_device", methods=["POST"])
def toggle_device():
    # Load current conditions
    conditions_data = load_conditions()

    # Get the device name from the request
    device = request.json.get("device")
    if device not in ["water_pump", "ventilation"]:
        return jsonify({"error": "Invalid device"}), 400

    # Determine the target GMS endpoint for the device
    gms_endpoint = f"http://{gms_url}/api/controls/{device}"

    # Toggle the state of the selected device
    try:
        # Get the current state from conditions.json
        current_state = conditions_data.get(f"{device}_state", "OFF")
        new_state = "ON" if current_state == "OFF" else "OFF"

        # Send the toggle request to the GMS API
        response = requests.put(gms_endpoint, json={"state": new_state}, timeout=10)

        if response.status_code == 200:
            print("I got here")
            # Update the state locally if the GMS API call is successful
            conditions_data[f"{device}_state"] = new_state

            # Save the updated state to the conditions file
            with open(conditions_file, 'w') as file:
                json.dump(conditions_data, file, indent=4)

            return jsonify({
                "device": device,
                "new_state": new_state
            })
        else:
            # Handle GMS API errors
            return jsonify({"error": f"GMS API error: {response.status_code}"}), 500

    except requests.RequestException as e:
        return jsonify({"error": f"Failed to communicate with GMS: {str(e)}"}), 500


if __name__ == "__main__":
    status_thread = threading.Thread(target=update_gms_status, daemon=True)
    status_thread.start()

    sensor_thread = threading.Thread(target=update_current_data, daemon=True)
    sensor_thread.start()

    app.run(port="8080", debug=True)