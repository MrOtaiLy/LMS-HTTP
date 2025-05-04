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


def get_pharmacy_color(pharmacy):
    try:
        hours = pharmacy["metaDataProperty"]["GeocoderMetaData"]["Hours"]["text"]
        if "круглосуточно" in hours.lower():
            return "pm2gnl"
        return "pm2blm"
    except KeyError:
        return "pm2grm"


def find_pharmacies(ll):
    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": API_KEY,
        "geocode": ll,
        "format": "json",
        "results": 50,
        "kind": "house",
        "text": "аптека",
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        features = data["response"]["GeoObjectCollection"]["featureMember"]
        if not features:
            return []

        orig_lon, orig_lat = map(float, ll.split(","))
        pharmacies = []

        for feature in features:
            geo_obj = feature["GeoObject"]
            pos = geo_obj["Point"]["pos"]
            lon, lat = map(float, pos.split())
            dist = haversine(orig_lon, orig_lat, lon, lat)
            pharmacies.append((dist, geo_obj))

        pharmacies.sort(key=lambda x: x[0])
        return [pharmacy[1] for pharmacy in pharmacies[:10]]
    except Exception as e:
        print(f"Ошибка поиска аптек: {e}")
        return []


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

        pharmacies = find_pharmacies(orig_ll)
        if not pharmacies:
            print("Аптеки не найдены")
            sys.exit(1)

        points = [f"{orig_ll},pm2rdm"]
        pharmacy_data = []
        all_points = [orig_ll]

        for pharmacy in pharmacies:
            pos = pharmacy["Point"]["pos"].replace(" ", ",")
            all_points.append(pos)
            color = get_pharmacy_color(pharmacy)
            points.append(f"{pos},{color}")

            lon, lat = map(float, pos.split(","))
            distance = round(haversine(orig_lon, orig_lat, lon, lat))
            name = pharmacy.get("name", "Название отсутствует")
            addr = pharmacy.get("description", "Адрес отсутствует")
            pharmacy_data.append((name, addr, distance))

        lons = [float(p.split(",")[0]) for p in all_points]
        lats = [float(p.split(",")[1]) for p in all_points]
        center_lon = (max(lons) + min(lons)) / 2
        center_lat = (max(lats) + min(lats)) / 2
        spn = get_spn(all_points)

        show_map(f"{center_lon},{center_lat}", spn, points)

        print("\nНайденные аптеки:")
        for i, (name, addr, dist) in enumerate(pharmacy_data, 1):
            print(f"{i}. {name}")
            print(f"   Адрес: {addr}")
            print(f"   Расстояние: {dist} метров\n")

    except Exception as e:
        print(f"Произошла ошибка: {e}")
