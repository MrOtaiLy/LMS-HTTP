def get_spn(geocoder_result):
    envelope = geocoder_result["response"]["GeoObjectCollection"]["featureMember"][0][
        "GeoObject"
    ]["boundedBy"]["Envelope"]
    lower = list(map(float, envelope["lowerCorner"].split()))
    upper = list(map(float, envelope["upperCorner"].split()))

    dx = abs(upper[0] - lower[0]) / 2
    dy = abs(upper[1] - lower[1]) / 2
    return f"{dx},{dy}"