import sys
import math
import requests

API_KEY = "af8378fd-9ded-4076-99e2-636abd678ba7"


def haversine(lon1, lat1, lon2, lat2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * (
        math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def geocode(address):
    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {"apikey": API_KEY, "geocode": address, "format": "json"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise Exception(f"Ошибка геокодирования: {e}")


def get_spn(points):
    lons = [float(p.split(",")[0]) for p in points]
    lats = [float(p.split(",")[1]) for p in points]
    delta_lon = abs(max(lons) - min(lons)) * 1.2
    delta_lat = abs(max(lats) - min(lats)) * 1.2
    return f"{delta_lon},{delta_lat}"


def find_nearest_pharmacy(ll):
    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": API_KEY,
        "geocode": ll,
        "format": "json",
        "results": 10,
        "kind": "house",
        "text": "аптека",
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        features = data["response"]["GeoObjectCollection"]["featureMember"]
        if not features:
            return None

        closest = None
        min_distance = float("inf")
        orig_lon, orig_lat = map(float, ll.split(","))

        for feature in features:
            pos = feature["GeoObject"]["Point"]["pos"]
            lon, lat = map(float, pos.split())
            dist = haversine(orig_lon, orig_lat, lon, lat)
            if dist < min_distance:
                min_distance = dist
                closest = feature["GeoObject"]

        return closest
    except Exception as e:
        print(f"Ошибка поиска аптеки: {e}")
        return None


def show_map(ll, spn, points):
    url = "https://static-maps.yandex.ru/1.x/"
    params = {"ll": ll, "spn": spn, "l": "map", "pt": "~".join(points)}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        with open("map.png", "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f"Ошибка загрузки карты: {e}")


if __name__ == "__main__":
    address = input("Введите адрес: ").strip()

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

        pharmacy = find_nearest_pharmacy(orig_ll)
        if not pharmacy:
            print("Аптеки не найдены")
            sys.exit(1)

        pharmacy_pos = pharmacy["Point"]["pos"].replace(" ", ",")
        pharmacy_lon, pharmacy_lat = map(float, pharmacy_pos.split(","))
        distance = round(haversine(orig_lon, orig_lat, pharmacy_lon, pharmacy_lat))

        points = [f"{orig_ll},pm2rdm", f"{pharmacy_pos},pm2gnm"]
        center_lon = (orig_lon + pharmacy_lon) / 2
        center_lat = (orig_lat + pharmacy_lat) / 2
        spn = get_spn([orig_ll, pharmacy_pos])

        show_map(f"{center_lon},{center_lat}", spn, points)

        print(
            f"""
Исходный адрес: {address}
Найденная аптека: {pharmacy.get('name', 'Название отсутствует')}
Адрес: {pharmacy.get('description', 'Адрес отсутствует')}
Расстояние: {distance} метров
"""
        )

    except Exception as e:
        print(f"Произошла ошибка: {e}")
