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
    dlambda = math.radians(lon2 - lon1)
    return (
        math.acos(
            math.sin(phi1) * math.sin(phi2)
            + math.cos(phi1) * math.cos(phi2) * math.cos(dlambda)
        )
        * R
    )


def get_point_color(hours):
    if not hours:
        return "gr"
    if "круглосуточно" in hours.get("text", "").lower():
        return "gn"
    return "bl"


def find_pharmacies(ll):
    search_api = "https://search-maps.yandex.ru/v1/"
    params = {
        "apikey": API_KEY,
        "text": "аптека",
        "ll": ll,
        "type": "biz",
        "lang": "ru_RU",
        "results": 10,
    }
    try:
        response = requests.get(search_api, params=params)
        response.raise_for_status()
        return response.json().get("features", [])
    except Exception as e:
        print(f"Ошибка поиска аптек: {e}")
        return []


def show_map(ll, spn, points):
    map_api = "https://static-maps.yandex.ru/1.x/"
    params = {"ll": ll, "spn": spn, "l": "map", "pt": "~".join(points)}
    try:
        response = requests.get(map_api, params=params)
        response.raise_for_status()
        with open("map.png", "wb") as f:
            f.write(response.content)
    except Exception as e:
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

        pharmacies = find_pharmacies(orig_ll)
        if not pharmacies:
            print("Аптеки не найдены")
            sys.exit(1)

        points = [f"{orig_ll},pm2rdm"]
        pharmacies_info = []
        all_coords = [orig_ll]

        for pharma in pharmacies:
            coords = pharma["geometry"]["coordinates"]
            pharma_ll = f"{coords[0]},{coords[1]}"
            all_coords.append(pharma_ll)

            meta = pharma["properties"]["CompanyMetaData"]
            hours = meta.get("Hours", {})
            color = get_point_color(hours)

            points.append(f"{pharma_ll},pm2{color}m")
            distance = round(haversine(orig_lon, orig_lat, coords[0], coords[1]))

            pharmacies_info.append(
                {
                    "name": meta.get("name", "Без названия"),
                    "address": meta.get("address", "Адрес не указан"),
                    "hours": hours.get("text", "Нет данных"),
                    "distance": distance,
                }
            )

        lons = [float(c.split(",")[0]) for c in all_coords]
        lats = [float(c.split(",")[1]) for c in all_coords]
        center_lon = (max(lons) + min(lons)) / 2
        center_lat = (max(lats) + min(lats)) / 2

        show_map(f"{center_lon},{center_lat}", get_spn(all_coords), points)

        print(f"\nНайдено аптек: {len(pharmacies_info)}\n")
        for i, pharma in enumerate(pharmacies_info, 1):
            print(f"{i}. {pharma['name']}")
            print(f"   Адрес: {pharma['address']}")
            print(f"   Режим работы: {pharma['hours']}")
            print(f"   Расстояние: {pharma['distance']} м\n")

    except Exception as e:
        print(f"Ошибка: {e}")
