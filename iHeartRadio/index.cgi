#!/usr/bin/env python3

from cgi import FieldStorage
from sys import stdout
import requests

print("Content-Type: audio/x-scpls; charset=UTF-8")
print("Content-Disposition: inline; filename=\"iheart.pls\"\n")

print("[Playlist]")

form = FieldStorage()
base_url = "https://api.iheart.com"
catalog = "/api/v1/catalog/searchAll"

keyword = ""
search_url = f"{base_url}{catalog}"
params = {}

if "q" in form:
    keyword = form["q"].value
    params = {
        "keywords": keyword,
        "bestMatch": "true",
        "limit": 10
        "querystation": "true"
    }

i = 1

if keyword:
    try:
        response = requests.get(search_url, params=params, headers={"User-Agent": "iHeartCGI-Proxy/1.0"})

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])

            for item in results:
                if item.get("type") == "liveStation" or "streams" in item:
                    station_name = item.get("name", "Unknown Station")
                    streams = item.get("streams", {})
                
                # Prioritize Shoutcast/Icecast URLs 
                stream_url = streams.get("shoutcast") or streams.get("secureShoutcast")
                
                if stream_url:
                    stdout.write(f"File{i}={stream_url}\n")
                    stdout.write(f"Title{i}={station_name}\n")
                    stdout.write(f"Length{i}=-1\n") # -1 denotes a live web stream
                    i += 1

        stdout.write(f"NumberOfEntries={i - 1}\n")
        stdout.write("Version=2\n")
    else:
        stdout.write(f"File1=http://error\nTitle1=Error: iHeart API returned code {response.status_code}\nNumberOfEntries=1\nVersion=2\n")

    except Exception as e:
        stdout.write(f"File1=http://error\nTitle1=Exception: {str(e)}\nNumberOfEntries=1\nVersion=2\n")
else:
    stdout.write("File1=http://error\nTitle1=Error: Provide ?q= search keyword\nNumberOfEntries=1\nVersion=2\n")
