import re
import json

from settings import redis_client


def validate_and_save_field(user_id, field, value):
    user_data = json.loads(redis_client.get(user_id))
    clean_func = EDIT_FIELDS[field]
    try:
        cleaned_value = clean_func(value)
        user_data[field] = cleaned_value
        redis_client.set(user_id, json.dumps(user_data))
        return True, None
    except ValueError:
        return False, f"Invalid {field}. Please enter a valid value."


def clean_price(price: str) -> int:
    return int("".join(re.findall(r"\d+", price)))


def clean_area(area: str) -> int:
    return int("".join(re.findall(r"\d+", area)))


def clean_rooms(rooms: str) -> str:
    return rooms


def clean_building(building: str) -> str:
    return building


def clean_district(district: str) -> str:
    return district


def clean_text(text: str) -> str:
    return text


EDIT_FIELDS = {
    "price": clean_price,
    "rooms": clean_rooms,
    "text": clean_text,
    "area": clean_area,
    "building": clean_building,
    "district": clean_district,
}
