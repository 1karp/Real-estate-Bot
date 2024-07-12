import requests


URL = "http://localhost:8000/ads"


def save_ad_to_db(user_id, data):
    url = URL
    photos_str = ",".join(data["photos"])

    ad_data = {
        "user_id": user_id,
        "username": data["username"],
        "photos": photos_str,
        "rooms": data["rooms"],
        "price": data["price"],
        "type": data["type"],
        "area": data["area"],
        "house_name": data["house_name"],
        "district": data["district"],
        "text": data["text"],
    }

    response = requests.post(url, json=ad_data)
    if response.status_code == 201:
        ad_id = response.json().get("id")
        return ad_id
    else:
        response.raise_for_status()


def fetch_ad_by_id(ad_id):
    url = URL + f"/{ad_id}"
    response = requests.get(url)

    if response.status_code == 200:
        ad_data = response.json()
        photos = ad_data["photos"].split(",")
        return (
            ad_data["username"],
            photos,
            ad_data["rooms"],
            ad_data["price"],
            ad_data["type"],
            ad_data["area"],
            ad_data["house_name"],
            ad_data["district"],
            ad_data["text"],
        )
    else:
        response.raise_for_status()


def fetch_ads_by_username(username):
    url = URL + f"?username={username}"
    response = requests.get(url)

    if response.status_code == 200:
        ads_data = response.json()
        ads = []
        for ad in ads_data:
            photos = ad["photos"].split(",")
            ads.append(
                (
                    ad["id"],
                    photos,
                    ad["rooms"],
                    ad["price"],
                    ad["type"],
                    ad["area"],
                    ad["house_name"],
                    ad["district"],
                    ad["text"],
                )
            )
        return ads if ads else None
    else:
        response.raise_for_status()
