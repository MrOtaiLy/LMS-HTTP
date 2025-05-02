import requests
from map_params import get_spn

api_key = "KEY" 

def geocode(address):
    geocoder_api = "http://geocode-maps.yandex.ru/1.x/"
    params = {"apikey": api_key, "geocode": address, "format": "json"}
    response = requests.get(geocoder_api, params=params)
    return response.json()


def show_map(ll, spn, pt):
    map_api = "https://static-maps.yandex.ru/1.x/"
    params = {"ll": ll, "spn": spn, "l": "map", "pt": pt}
    response = requests.get(map_api, params=params)
    with open("map.png", "wb") as f:
        f.write(response.content)


if __name__ == "__main__":
    address = input("Введите адрес: ")
    geocoder_result = geocode(address)
    pos = geocoder_result["response"]["GeoObjectCollection"]["featureMember"][0][
        "GeoObject"
    ]["Point"]["pos"]
    ll = pos.replace(" ", ",")

    spn = get_spn(geocoder_result)

    pt = f"{ll},pm2rdm"
    show_map(ll, spn, pt)
    print("Карта сохранена как map.png")