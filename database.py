import json

import requests

from settings import redis_client

URL_ADS = "http://localhost:8000/ads"
URL_USERS = "http://localhost:8000/users"


def save_user_to_db(user_id, username):
    url = URL_USERS
    data = {"userid": user_id, "username": username, "ads": ""}
    requests.post(url, json=data)


def save_ad_to_db(user_id, data):
    url = URL_ADS
    photos_str = ",".join(data["photos"])

    ad_data = {
        "user_id": data["user_id"],
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


def load_ad_by_id(ad_id):
    url = URL_ADS + f"/{ad_id}"
    response = requests.get(url)

    if response.status_code == 200:
        ad_data = response.json()
        redis_client.set(ad_data.get("user_id"), json.dumps(ad_data))
    else:
        response.raise_for_status()


def update_ad(user_id):
    ad_data = json.loads(redis_client.get(user_id))
    url = URL_ADS + f"/{ad_data['id']}"

    response = requests.put(url, json=ad_data)
    if response.status_code == 200:
        return True
    else:
        response.raise_for_status()


def fetch_ads_by_userid(userid):
    url = URL_ADS + f"?userid={userid}"
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
    url = URL_ADS + f"/{ad_id}/post"
    response = requests.post(url)

    if response.status_code == 200:
        return True
    else:
        return False
        response.raise_for_status()


def edit_post_ad(ad_id):
    url = URL_ADS + f"/{ad_id}/edit-post"
    response = requests.post(url)
    if response.status_code == 200:
        return True
    else:
        return False
        response.raise_for_status()
