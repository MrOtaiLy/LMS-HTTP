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
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * (
        math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def geocode(address):
    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {"apikey": GEOCODER_API_KEY, "geocode": address, "format": "json"}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def get_pharmacy_color(hours):
    if hours:
        if "круглосуточно" in hours.lower():
            return "pm2gnm"
        return "pm2blm"
    return "pm2grm"


def find_pharmacies(ll):
    url = "https://search-maps.yandex.ru/v1/"
    params = {
        "apikey": SEARCH_API_KEY,
        "text": "аптека",
        "ll": ll,
        "type": "biz",
        "lang": "ru_RU",
        "results": 50,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    features = data.get("features", [])
    orig_lon, orig_lat = map(float, ll.split(","))
    pharmacies = []
    for f in features:
        c = f["geometry"]["coordinates"]
        dist = haversine(orig_lon, orig_lat, c[0], c[1])
        pharmacies.append((dist, f))
    pharmacies.sort(key=lambda x: x[0])
    return pharmacies[:10]


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
        response = requests.get(url, params=params)
        response.raise_for_status()
        tmp_file.write(response.content)
        tmp_file.flush()
        app = QApplication(sys.argv)
        w = MapWindow(tmp_file.name)
        w.show()
        app.exec()


def get_spn(points):
    lons = [float(p.split(",")[0]) for p in points]
    lats = [float(p.split(",")[1]) for p in points]
    delta_lon = abs(max(lons) - min(lons)) * 1.2
    delta_lat = abs(max(lats) - min(lats)) * 1.2
    return f"{delta_lon},{delta_lat}"


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
        pharmacies = find_pharmacies(orig_ll)
        if not pharmacies:
            print("Аптеки не найдены")
            sys.exit(1)
        all_points = [orig_ll]
        points = [f"{orig_ll},pm2rdm"]
        results = []
        for i, (dist, ph) in enumerate(pharmacies, start=1):
            meta = ph["properties"].get("CompanyMetaData", {})
            name = meta.get("name", "Название отсутствует")
            addr = meta.get("address", "Адрес отсутствует")
            hrs = meta.get("Hours", {}).get("text", "")
            c = ph["geometry"]["coordinates"]
            color = get_pharmacy_color(hrs)
            results.append((i, name, addr, hrs, round(dist)))
            ph_ll = f"{c[0]},{c[1]}"
            all_points.append(ph_ll)
            points.append(f"{ph_ll},{color}")
        lons = [float(p.split(",")[0]) for p in all_points]
        lats = [float(p.split(",")[1]) for p in all_points]
        center_lon = (max(lons) + min(lons)) / 2
        center_lat = (max(lats) + min(lats)) / 2
        spn = get_spn(all_points)
        print("Найденные аптеки:")
        for i, n, a, h, d in results:
            print(f"{i}. {n}")
            print(f"   Адрес: {a}")
            print(f"   Время работы: {h if h else 'не указано'}")
            print(f"   Расстояние: {d} метров\n")
        show_map(f"{center_lon},{center_lat}", spn, points)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
