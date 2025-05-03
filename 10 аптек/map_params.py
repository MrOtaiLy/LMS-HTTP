def get_spn(coords):
    lons = [float(c.split(",")[0]) for c in coords]
    lats = [float(c.split(",")[1]) for c in coords]

    delta_lon = (max(lons) - min(lons)) * 1.1
    delta_lat = (max(lats) - min(lats)) * 1.1

    return f"{delta_lon},{delta_lat}"
