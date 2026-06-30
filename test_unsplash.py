import requests
KEY = "kU8MC5zwSkJEwNIFFgNXx3yy1vjhtjwHxNW6dADiHmI"   # paste the raw key, no quotes tricks
r = requests.get(
    "https://api.unsplash.com/search/photos",
    headers={"Authorization": f"Client-ID {KEY}"},
    params={"query": "Nike", "per_page": 3}
)
print("Status:", r.status_code)
print("Response:", r.json())
