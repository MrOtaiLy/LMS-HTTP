import sys
import math
import argparse
import requests
from geocode import geocode
from map_params import get_spn

API_KEY = "KEY" #У меня не работает ни один ключ почему-то, поэтому заглушка


def haversine(lon1, lat1, lon2, lat2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_pharmacy(ll):
    search_api = "https://search-maps.yandex.ru/v1/"
    params = {
        "apikey": API_KEY,
        "text": "аптека",
        "ll": ll,
        "type": "biz",
        "lang": "ru_RU",
        "results": 1,
    }
    try:
        response = requests.get(search_api, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка поиска аптеки: {e}")
        return None


def show_map(ll, spn, points):
    map_api = "https://static-maps.yandex.ru/1.x/"
    params = {"ll": ll, "spn": spn, "l": "map", "pt": "~".join(points)}
    try:
        response = requests.get(map_api, params=params)
        response.raise_for_status()
        with open("map.png", "wb") as f:
            f.write(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Ошибка загрузки карты: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("address", nargs="+", help="Адрес для поиска")
    args = parser.parse_args()
    address = " ".join(args.address)

    try:
        geo_data = geocode(address)
        if not geo_data["response"]["GeoObjectCollection"]["featureMember"]:
            print("Адрес не найден")
            sys.exit(1)

        pos = geo_data["response"]["GeoObjectCollection"]["featureMember"][0][
            "GeoObject"
        ]["Point"]["pos"]
        orig_ll = pos.replace(" ", ",")
        orig_lon, orig_lat = map(float, orig_ll.split(","))

        pharmacy_data = find_pharmacy(orig_ll)
        if not pharmacy_data or not pharmacy_data.get("features"):
            print("Аптеки не найдены")
            sys.exit(1)

        pharmacy = pharmacy_data["features"][0]
        pharmacy_coords = pharmacy["geometry"]["coordinates"]
        pharmacy_pos = f"{pharmacy_coords[0]},{pharmacy_coords[1]}"
        pharmacy_lon, pharmacy_lat = pharmacy_coords

        distance = round(haversine(orig_lon, orig_lat, pharmacy_lon, pharmacy_lat))

        meta = pharmacy["properties"]["CompanyMetaData"]
        points = [f"{orig_ll},pm2rdm", f"{pharmacy_pos},pm2gnm"]

        center_lon = (orig_lon + pharmacy_lon) / 2
        center_lat = (orig_lat + pharmacy_lat) / 2
        spn = get_spn([orig_ll, pharmacy_pos])

        show_map(f"{center_lon},{center_lat}", spn, points)

        print(
            f"""
        Исходный адрес: {address}
        Найденная аптека: {meta.get('name', 'Название отсутствует')}
        Адрес: {meta.get('address', 'Адрес отсутствует')}
        Режим работы: {meta.get('Hours', {}).get('text', 'Нет данных')}
        Расстояние: {distance} метров
        """
        )

    except Exception as e:
        print(f"Произошла ошибка: {e}")
