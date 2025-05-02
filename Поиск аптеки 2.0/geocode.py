import requests

API_KEY = "KEY" #У меня не работает ни один ключ почему-то, поэтому заглушка

def geocode(address):
    geocoder_api = "http://geocode-maps.yandex.ru/1.x/"
    params = {"apikey": API_KEY, "geocode": address, "format": "json"}
    try:
        response = requests.get(geocoder_api, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ошибка геокодирования: {e}")
