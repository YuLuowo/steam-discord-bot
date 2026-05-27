import requests
import json
import os

WEBHOOK_URL = os.environ["WEBHOOK_URL"]

API_URL = "https://store.steampowered.com/api/featuredcategories/?cc=tw&l=chinese"

def get_app_details(appid):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=tw&l=chinese"
    res = requests.get(url).json()

    data = res.get(str(appid), {}).get("data")
    if not data:
        return None

    price = data.get("price_overview")
    if not price:
        return None

    return {
        "name": data["name"],
        "image": data.get("header_image"),
        "original": price["initial"] / 100,
        "final": price["final"] / 100,
        "currency": price.get("currency", "TWD"),
        "discount": price["discount_percent"],
        "reviews": data.get("recommendations", {}).get("total", 0),
        "appid": appid
    }

try:
    with open("seen.json", "r") as f:
        seen = set(json.load(f))
except:
    seen = set()

data = requests.get(API_URL).json()
items = data.get("specials", {}).get("items", [])

candidates = []

for game in items:
    appid = game["id"]

    if appid in seen:
        continue

    details = get_app_details(appid)
    if not details:
        continue

    if details["discount"] < 50:
        continue

    candidates.append(details)
    seen.add(appid)

candidates = sorted(candidates, key=lambda x: x["discount"], reverse=True)[:5]

def format_price(price):
    return f"NT$ {price:,.0f}"

for g in candidates:
    payload = {
        "embeds": [
            {
                "title": f"Steam 精選折扣",
                "description": (
                    f"**{g['name']}**\n\n"
                    f"{format_price(g['original'])} → {format_price(g['final'])}（-{g['discount']}%）\n"
                    f"評論數：{g['reviews']:,}\n\n"
                    f"[查看遊戲](https://store.steampowered.com/app/{g['appid']})"
                ),
                "color": 0x1b2838,
                "image": {
                    "url": g["image"]
                }
            }
        ]
    }

    requests.post(WEBHOOK_URL, json=payload)

with open("seen.json", "w") as f:
    json.dump(list(seen), f)