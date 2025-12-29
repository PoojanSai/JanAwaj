import requests

def get_location_details(lat, lon):
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json"
    }

    res = requests.get(url, params=params, headers={"User-Agent": "JanAwaJ"})
    data = res.json()

    address = data.get("address", {})
    district = address.get("county") or address.get("district")
    state = address.get("state")

    return district, state
