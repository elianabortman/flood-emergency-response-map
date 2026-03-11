import requests


class WeatherService:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_weather(self, lat, lon):
        url = "https://api.openweathermap.org/data/2.5/weather"f"?lat={lat}&lon={lon}&appid={self.api_key}&units=metric"
        response = requests.get(url)
        data = response.json()
        return {
            "temperature": data["main"]["temp"],
            "wind_speed": data["wind"]["speed"],
            "precipitation": data.get("rain", {}).get("1h", 0),
        }
