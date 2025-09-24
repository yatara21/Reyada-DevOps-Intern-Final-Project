from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import requests
import matplotlib.pyplot as plt
import io
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Database and API configuration
#weather_data.db
DB_FILE = '/mnt/weatherdata/weather_data.db'
API_KEY = os.getenv('OPENWEATHER_API_KEY')

# Ensure database and static directory exist
def init_app():
    # Create static directory if not exists
    os.makedirs('static', exist_ok=True)

    # Initialize database
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS weather (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT NOT NULL,
                    temperature REAL,
                    humidity INTEGER,
                    description TEXT
                )
            ''')
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add_city', methods=['POST'])
def add_city():
    city = request.form['city']
    if not city:
        return redirect(url_for('home'))

    # Fetch weather data
    try:
        weather_data = fetch_weather(city)
        if weather_data:
            save_to_db(city, weather_data)
    except Exception as e:
        print(f"Error adding city: {e}")

    return redirect(url_for('home'))

@app.route('/weather')
def weather():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT city, temperature, humidity, description FROM weather')
            data = cursor.fetchall()
        return render_template('weather.html', weather_data=data)
    except sqlite3.Error as e:
        print(f"Database query error: {e}")
        return "An error occurred while fetching weather data", 500

@app.route('/plot')
def plot():
    try:
        # Generate a plot of weather data
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT city, temperature FROM weather')
            data = cursor.fetchall()

        cities = [row[0] for row in data]
        temperatures = [row[1] for row in data]

        plt.figure(figsize=(10, 6))
        plt.bar(cities, temperatures, color='skyblue')
        plt.title('City Temperatures')
        plt.xlabel('City')
        plt.ylabel('Temperature (°C)')
        plt.tight_layout()
        plt.savefig('static/plot.png')
        plt.close()  # Close the plot to free up memory
        return send_file('static/plot.png', mimetype='image/png')
    except Exception as e:
        print(f"Plot generation error: {e}")
        return "An error occurred while generating the plot", 500

def fetch_weather(city):
    try:
        url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        return {
            'temperature': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description']
        }
    except requests.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

def save_to_db(city, weather_data):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO weather (city, temperature, humidity, description)
                VALUES (?, ?, ?, ?)
            ''', (city, weather_data['temperature'], weather_data['humidity'], weather_data['description']))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database insertion error: {e}")

if __name__ == '__main__':
    init_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
