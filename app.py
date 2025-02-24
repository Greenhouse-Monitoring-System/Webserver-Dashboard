from flask import *
import json
import os
import time
import tomllib
import requests
import threading

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
                sensor_data['distance'] = round(sensor_data['distance'] * 100 / container_vol)
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

@app.route("/assistant")
def assistant():
    return render_template("assistant.html")

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