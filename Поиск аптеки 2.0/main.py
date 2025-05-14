import sys
import math
import requests
import tempfile
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

GEOCODER_API_KEY = "af8378fd-9ded-4076-99e2-636abd678ba7"
SEARCH_API_KEY = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"
STATIC_API_KEY = "059355dd-b624-4e9e-a139-88710341c3cb"


class MapWindow(QWidget):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Яндекс.Карты")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)

        pixmap = QPixmap(image_path)
        self.image_label.setPixmap(pixmap.scaledToWidth(800))


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


def geocode(address):
    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {"apikey": GEOCODER_API_KEY, "geocode": address, "format": "json"}
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
    url = "https://search-maps.yandex.ru/v1/"
    params = {
        "apikey": SEARCH_API_KEY,
        "text": "аптека",
        "ll": ll,
        "type": "biz",
        "lang": "ru_RU",
        "results": 10,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        features = data.get("features", [])

        if not features:
            return None

        orig_lon, orig_lat = map(float, ll.split(","))
        closest = None
        min_distance = float("inf")

        for feature in features:
            coords = feature["geometry"]["coordinates"]
            lon, lat = coords[0], coords[1]
            dist = haversine(orig_lon, orig_lat, lon, lat)
            if dist < min_distance:
                min_distance = dist
                closest = feature

        return closest
    except Exception as e:
        print(f"Ошибка поиска аптеки: {e}")
        return None


def show_map(ll, spn, points):
    url = "https://static-maps.yandex.ru/1.x/"
    params = {
        "ll": ll,
        "spn": spn,
        "l": "map",
        "pt": "~".join(points),
        "apikey": STATIC_API_KEY,
    }

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            tmp_file.write(response.content)
            tmp_file.flush()

            app = QApplication(sys.argv)
            window = MapWindow(tmp_file.name)
            window.show()
            app.exec()

        except Exception as e:
            print(f"Ошибка загрузки карты: {e}")


if __name__ == "__main__":
    address = input("Введите адрес: ").strip()

    try:
        geo_data = geocode(address)
        members = geo_data["response"]["GeoObjectCollection"]["featureMember"]
        if not members:
            print("Адрес не найден")
            sys.exit(1)

        pos = members[0]["GeoObject"]["Point"]["pos"]
        orig_ll = pos.replace(" ", ",")
        orig_lon, orig_lat = map(float, orig_ll.split(","))

        pharmacy = find_nearest_pharmacy(orig_ll)
        if not pharmacy:
            print("Аптеки не найдены")
            sys.exit(1)

        meta = pharmacy["properties"].get("CompanyMetaData", {})
        name = meta.get("name", "Название отсутствует")
        address_pharm = meta.get("address", "Адрес отсутствует")
        hours = meta.get("Hours", {}).get("text", "Время работы не указано")

        coords = pharmacy["geometry"]["coordinates"]
        pharmacy_lon, pharmacy_lat = coords[0], coords[1]
        distance = round(haversine(orig_lon, orig_lat, pharmacy_lon, pharmacy_lat))

        points = [f"{orig_ll},pm2rdm", f"{coords[0]},{coords[1]},pm2gnm"]
        center_lon = (orig_lon + pharmacy_lon) / 2
        center_lat = (orig_lat + pharmacy_lat) / 2
        spn = get_spn([orig_ll, f"{coords[0]},{coords[1]}"])

        print(
            f"""
Исходный адрес: {address}
Найденная аптека: {name}
Адрес: {address_pharm}
Время работы: {hours}
Расстояние: {distance} метров
"""
        )

        show_map(f"{center_lon},{center_lat}", spn, points)

    except Exception as e:
        print(f"Произошла ошибка: {e}")
