def get_spn(points):
    lons = [float(p.split(",")[0]) for p in points]
    lats = [float(p.split(",")[1]) for p in points]

    delta_lon = abs(max(lons) - min(lons)) * 1.2
    delta_lat = abs(max(lats) - min(lats)) * 1.2

    return f"{delta_lon},{delta_lat}"
