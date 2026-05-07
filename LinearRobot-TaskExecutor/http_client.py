import requests

url = "http://localhost:5173/api/layout/boxes"

res = requests.get(url)

if res.status_code == 200:
    print("Response:", res.json()["data"])
else:
    print("Error:", res.status_code, res.text)
