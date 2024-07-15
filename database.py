import requests
import json

from settings import redis_client


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
        "building": data["building"],
        "district": data["district"],
        "text": data["text"],
    }

    response = requests.post(url, json=ad_data)
    if response.status_code == 201:
        ad_id = response.json().get("id")
        return ad_id
    else:
        response.raise_for_status()


def load_ad_by_id(ad_id, user_id):
    url = URL + f"/{ad_id}"
    response = requests.get(url)

    if response.status_code == 200:
        ad_data = response.json()
        redis_client.set(user_id, json.dumps(ad_data))
    else:
        response.raise_for_status()


def update_ad(user_id):
    ad_data = json.loads(redis_client.get(user_id))
    url = URL + f"/{ad_data['id']}"

    response = requests.put(url, json=ad_data)
    if response.status_code == 200:
        return True
    else:
        response.raise_for_status()


def fetch_ads_by_userid(userid):
    url = URL + f"?userid={userid}"
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
                    ad["building"],
                    ad["district"],
                    ad["text"],
                )
            )
        return ads if ads else None
    else:
        response.raise_for_status()


def post_ad(ad_id):
    url = URL + f"/{ad_id}/post"
    response = requests.post(url)

    if response.status_code == 200:
        return True
    else:
        return False
        response.raise_for_status()
