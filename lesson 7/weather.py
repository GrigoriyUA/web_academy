import requests
from cities import CITIES

API_URL = "https://api.open-meteo.com/v1/forecast"

WMO_CODES = {
    0:  "Ясно",
    1:  "Переважно ясно",
    2:  "Мінлива хмарність",
    3:  "Хмарно",
    45: "Туман",
    48: "Туман з інеєм",
    51: "Легка мряка",
    53: "Мряка",
    55: "Густа мряка",
    61: "Слабкий дощ",
    63: "Помірний дощ",
    65: "Сильний дощ",
    71: "Слабкий сніг",
    73: "Помірний сніг",
    75: "Сильний сніг",
    77: "Снігові зерна",
    80: "Невеликий зливовий дощ",
    81: "Зливовий дощ",
    82: "Сильний зливовий дощ",
    85: "Снігова злива",
    86: "Сильна снігова злива",
    95: "Гроза",
    96: "Гроза з градом",
    99: "Гроза із сильним градом",
}

WEATHER_ICONS = {
    0:  "☀️",
    1:  "🌤",
    2:  "⛅",
    3:  "☁️",
    45: "🌫",
    48: "🌫",
    51: "🌦",
    53: "🌦",
    55: "🌧",
    61: "🌧",
    63: "🌧",
    65: "🌧",
    71: "🌨",
    73: "🌨",
    75: "❄️",
    77: "🌨",
    80: "🌦",
    81: "🌧",
    82: "⛈",
    85: "🌨",
    86: "❄️",
    95: "⛈",
    96: "⛈",
    99: "⛈",
}


def get_forecast(city_name: str, date_str: str) -> dict | None:
    """Fetch weather forecast for a city on a specific date.

    Args:
        city_name: Ukrainian name of the city (key in CITIES)
        date_str: Date in 'YYYY-MM-DD' format

    Returns:
        Dict with weather data or None on error.
    """
    city = CITIES.get(city_name)
    if not city:
        return None

    params = {
        "latitude": city["lat"],
        "longitude": city["lon"],
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,weathercode",
        "timezone": "Europe/Kyiv",
        "forecast_days": 10,
    }

    try:
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return None

    daily = data.get("daily", {})
    dates = daily.get("time", [])

    if date_str not in dates:
        return None

    idx = dates.index(date_str)

    code = daily["weathercode"][idx]
    return {
        "temp_max":     round(daily["temperature_2m_max"][idx]),
        "temp_min":     round(daily["temperature_2m_min"][idx]),
        "precipitation": daily["precipitation_sum"][idx] or 0.0,
        "wind_speed":   round(daily["wind_speed_10m_max"][idx]),
        "description":  WMO_CODES.get(code, "Невідомо"),
        "icon":         WEATHER_ICONS.get(code, "🌡"),
    }
