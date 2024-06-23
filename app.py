from flask import Flask, render_template, request, jsonify
import requests
import json
import sqlite3

app = Flask(__name__)


with open('config.json') as config_file:
    config = json.load(config_file)

# Function to get weather
def get_weather(location):
    api_key = config['weather_api_key']
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
    response = requests.get(url)
    return response.json()

# Option to get five-day
def get_forecast(location):
    api_key = config['weather_api_key']
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}&units=metric"
    response = requests.get(url)
    return response.json()

# Interaction log
def log_interaction(user_input, bot_response):
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    c.execute("INSERT INTO interactions (user_input, bot_response) VALUES (?, ?)", (user_input, bot_response))
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.form['user_input']
    response = "I can help you with weather updates. Ask me about the weather in any city."

    if "weather" in user_input.lower():
        words = user_input.split()
        if len(words) > 1:
            location = words[-1]
            weather_data = get_weather(location)
            if weather_data.get('cod') != 200:
                response = "Sorry, I couldn't find the weather information for that location."
            else:
                temp = weather_data['main']['temp']
                description = weather_data['weather'][0]['description']
                response = (f"The weather in {location} is {temp}°C with {description}. "
                            f"Would you like a five-day forecast?")
                log_interaction(user_input, response)
                return jsonify({'response': response, 'follow_up': True, 'location': location})
        else:
            response = "Please specify a location to get the weather information."
    else:
        response = str(response)

    log_interaction(user_input, response)
    return jsonify({'response': response, 'follow_up': False})

@app.route('/get_forecast', methods=['POST'])
def get_forecast_response():
    location = request.form['location']
    forecast_data = get_forecast(location)
    forecast_list = forecast_data.get('list', [])
    if not forecast_list:
        response = "Sorry, I couldn't find the forecast information for that location."
        log_interaction(location, response)
        return jsonify({'response': response})

    forecast_response = f"Five-day forecast for {location}:\n"
    for i in range(0, len(forecast_list), 8):  # Multiple entries
        day_data = forecast_list[i]
        date = day_data['dt_txt'].split(' ')[0]
        temp = day_data['main']['temp']
        description = day_data['weather'][0]['description']
        forecast_response += f"{date}: {temp}°C with {description}\n"

    log_interaction(f"Five-day forecast for {location}", forecast_response)
    return jsonify({'response': forecast_response})

if __name__ == '__main__':
    app.run(debug=True, port=8080)
