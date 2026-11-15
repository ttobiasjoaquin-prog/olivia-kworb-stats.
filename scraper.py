import json
import os
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

URL_SONGS = "https://kworb.net"
DATA_FILE = "data.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

ALBUMS = {
    "SOUR": [
        "brutal", "traitor", "drivers license", "1 step forward, 3 steps back",
        "deja vu", "good 4 u", "enough for you", "happier",
        "jealousy, jealousy", "favorite crime", "hope ur ok"
    ],
    "GUTS (spilled)": [
        "all-american bitch", "bad idea right?", "vampire", "lacy",
        "ballad of a homeschooled girl", "making the bed", "logical",
        "get him back!", "love is embarrassing", "the grudge",
        "pretty isn't pretty", "teenage dream", "obsessed",
        "girl i've always been", "scared of my guitar", "stranger", "so american"
    ],
    "you seem pretty sad for a girl so in love": [
        "drop dead", "stupid song", "honeybee", "maggots for brains",
        "u + me = <3", "my way", "purple", "the cure", "begged",
        "what's wrong with me", "less", "expectations", "cigarette smoke"
    ]
}

def clean_number(text):
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else 0

def normalize_title(title):
    t = title.lower().strip()
    t = re.sub(r"\s*\(with.*?\)", "", t)
    t = re.sub(r"\s*\(feat.*?\)", "", t)
    return t

def load_previous_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def fetch_kworb_songs():
    urls = [
        URL_SONGS,
        f"https://allorigins.win{URL_SONGS}"
    ]
    html = ""
    for u in urls:
        try:
            r = requests.get(u, headers=HEADERS, timeout=30)
            if r.status_code == 200 and "drivers license" in r.text.lower():
                html = r.text
                break
        except Exception:
            continue

    soup = BeautifulSoup(html, "html.parser")
    songs_map = {}
    for row in soup.find_all("tr"):
        link = row.find("a")
        if not link:
            continue
        norm_title = normalize_title(link.get_text(strip=True))
        nums = [clean_number(td.get_text(strip=True)) for td in row.find_all("td") if re.match(r"^[\d,]+$", td.get_text(strip=True))]
        if len(nums) >= 2:
            total, daily = nums[:2]
            if norm_title not in songs_map or total > songs_map[norm_title]["total"]:
                songs_map[norm_title] = {"total": total, "daily": daily}
    return songs_map


def main():
    prev_data = load_previous_data().get("albums", {})
    kworb_songs = fetch_kworb_songs()

    output = {
        "date": datetime.utcnow().strftime("%A, %B %d, %Y"),
        "artist": "Olivia Rodrigo",
        "albums": {}
    }

    for album_name, tracks in ALBUMS.items():
        prev_tracks = prev_data.get(album_name, {}).get("tracks_dict", {})
        lines = []
        tracks_dict = {}

        for track in tracks:
            norm = normalize_title(track)
            current = kworb_songs.get(norm, {"total": 0, "daily": 0})
            total = current["total"]
            hoy = current["daily"]
            ayer = prev_tracks.get(track, {}).get("hoy", hoy)

            lines.append(f"{track}, {total}, {hoy}, {ayer}")
            tracks_dict[track] = {"total": total, "hoy": hoy, "ayer": ayer}

        output["albums"][album_name] = {
            "textarea_ready": "\n".join(lines),
            "tracks_dict": tracks_dict
        }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
