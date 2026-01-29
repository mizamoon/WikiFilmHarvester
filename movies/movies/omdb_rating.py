import csv
import os
import time
import requests


def enrich_csv(path):
    api_key = os.getenv("OMDB_API_KEY")
    if not api_key:
        print("OMDB_API_KEY not set")
        return

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = reader.fieldnames

    if "IMDb ID" not in fields:
        print('No column "IMDb ID"')
        return

    new_fields = []
    for f in fields:
        if f == "IMDb ID":
            new_fields.append("IMDb рейтинг")
        else:
            new_fields.append(f)

    for row in rows:
        imdb_id = row.get("IMDb ID", "").strip()
        rating = ""

        if imdb_id:
            try:
                r = requests.get(
                    "https://www.omdbapi.com/",
                    params={"i": imdb_id, "apikey": api_key},
                    timeout=10,
                )
                data = r.json()
                if data.get("Response") == "True":
                    rating = data.get("imdbRating", "")
            except Exception:
                pass

            time.sleep(0.2)

        row["IMDb рейтинг"] = rating
        row.pop("IMDb ID", None)

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=new_fields)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    import sys
    enrich_csv(sys.argv[1])