from flask import *
import json
import os
import time

app = Flask(__name__)
conditions_file = "conditions.json"

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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/greenhouse_home")
def greenhouse():
    conditions_data = load_conditions()
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
        
        print("HERE ARE THE UPDATED CONDITIONSSSSSSS", conditions_data)

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
        conditions_data = load_conditions()
        return jsonify({
            "conditions": conditions_data,
            "image_url": "http://127.0.0.1:8080/static/upload_imgs/current/now.jpg"  # Image hosted by Flask
        })

if __name__ == "__main__":
    app.run(port="8080", debug=True)