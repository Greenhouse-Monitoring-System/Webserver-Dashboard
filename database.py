import sqlite3
import time
from datetime import datetime
import json

DB_FILE = "DB/greenhouse.db"

# Database setup
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Create a table to store sensor data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL,
            humidity REAL,
            distance REAL,
            soil_moisture INTEGER,
            tvoc REAL,
            co2 REAL
        )
        """)
    conn.commit()
    conn.close()

# Function to save data to the database
def save_to_db(temperature, humidity, distance, soil_moisture, tvoc, co2):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO sensor_data (timestamp, temperature, humidity, distance, soil_moisture, tvoc, co2)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, temperature, humidity, distance, soil_moisture, tvoc, co2))
    conn.commit()
    conn.close()

def getRecent_from_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp, temperature, humidity, distance, soil_moisture, tvoc, co2 
        FROM sensor_data 
        ORDER BY id DESC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()

    if row:
        timestamp, temperature, humidity, distance, soil_moisture, tvoc, co2 = row
        return json.dumps({
            "timestamp": timestamp,
            "temperature": temperature,
            "humidity": humidity,
            "distance": distance,
            "soilMoisture": soil_moisture,
            "tvoc": tvoc,
            "co2": co2
        })
    return json.dumps({"error": "No data available"})

# Function to fetch all sensor data
def getAll_from_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp, temperature, humidity, distance, soil_moisture, tvoc, co2 
        FROM sensor_data 
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    data = [
        {
            "timestamp": row[0],
            "temperature": row[1],
            "humidity": row[2],
            "distance": row[3],
            "soilMoisture": row[4],
            "tvoc": row[5],
            "co2": row[6]
        }
        for row in rows
    ]
    return json.dumps(data)