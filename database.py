import json

import requests

from settings import redis_client

URL_ADS = "http://localhost:8000/ads"
URL_USERS = "http://localhost:8000/users"


def save_user_to_db(user_id, username) -> None:
    url = URL_USERS
    data = {"userid": user_id, "username": username}
    requests.post(url, json=data)


def save_ad_to_db(user_id) -> str:
    url = URL_ADS
    ad_data = json.loads(redis_client.get(user_id))
    response = requests.post(url, json=ad_data)

    if response.status_code == 201:
        return response.json().get("id")
    else:
        response.raise_for_status()


def load_ad_by_id(ad_id) -> None:
    url = URL_ADS + f"/{ad_id}"
    response = requests.get(url)

    if response.status_code == 200:
        ad_data = response.json()
        redis_client.set(ad_data.get("user_id"), json.dumps(ad_data))
    else:
        response.raise_for_status()


def update_ad(user_id) -> bool:
    ad_data = json.loads(redis_client.get(user_id))
    url = URL_ADS + f"/{ad_data['id']}"

    response = requests.put(url, json=ad_data)
    if response.status_code == 200:
        return True
    else:
        response.raise_for_status()


def get_ads_by_userid(userid) -> list[str]:
    url = URL_USERS + f"/{userid}/ads"
    response = requests.get(url)

    if response.status_code == 200:
        ads = response.json()
        ads = ads[0].split(",")
        return ads
    else:
        response.raise_for_status()


def post_ad(ad_id) -> bool:
    url = URL_ADS + f"/{ad_id}/post"
    response = requests.post(url)

    if response.status_code == 200:
        return True
    else:
        response.raise_for_status()


def edit_post_ad(ad_id) -> bool:
    url = URL_ADS + f"/{ad_id}/edit-post"
    response = requests.post(url)
    if response.status_code == 200:
        return True
    else:
        response.raise_for_status()
