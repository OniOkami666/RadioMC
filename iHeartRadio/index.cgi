#!/usr/bin/env -S python3 -u -W ignore
from cgi import FieldStorage
import json
import os
import ssl
import sys
import urllib.parse
import urllib.request

# HTTP Headers
sys.stdout.write("Content-Type: audio/x-mpegurl; charset=UTF-8\r\n")
sys.stdout.write('Content-Disposition: attachment; filename="iheart.m3u"\r\n\r\n')
sys.stdout.flush()

# Prevent FieldStorage stdin hang on GET requests
if os.environ.get('REQUEST_METHOD') == 'GET':
    os.environ.pop('CONTENT_LENGTH', None)
    os.environ.pop('CONTENT_TYPE', None)

# Read search query
form = FieldStorage()
q = form.getvalue("q", "")

if not q:
    query_string = os.environ.get('QUERY_STRING', '')
    params = urllib.parse.parse_qs(query_string)
    q = params.get('q', [''])[0]

q = q.strip() or "top"

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

output = ["#EXTM3U"]

try:
    api_url = f"https://api.iheart.com/api/v1/catalog/searchAll?keywords={urllib.parse.quote(q)}"
    req = urllib.request.Request(
        api_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )

    with urllib.request.urlopen(req, timeout=4, context=ssl_ctx) as resp:
        data = json.loads(resp.read().decode('utf-8'))

        stations = []
        if isinstance(data, dict):
            results = data.get('results', {})
            if isinstance(results, dict):
                stations = results.get('stations', [])
            elif isinstance(results, list):
                stations = results
            if not stations:
                stations = data.get('stations', [])

        # Process up to 10 stations 
        for station in stations[:10]:
            if not isinstance(station, dict):
                continue

            name = (
                station.get('name')
                or station.get('callLetters')
                or 'iHeart Station'
            )
            station_id = station.get('id')
            if not station_id:
                continue

            # Extract station logo URL
            logo = (
                station.get('logo')
                or station.get('logoPath')
                or station.get('imagePath')
                or ''
            )
            if isinstance(logo, dict):
                logo_url = logo.get('url', '')
            else:
                logo_url = str(logo)

            if logo_url:
                if logo_url.startswith('//'):
                    logo_url = f"https:{logo_url}"
                # Append extension hint if missing 
                if not any(
                    logo_url.lower().endswith(ext)
                    for ext in ['.png', '.jpg', '.jpeg']
                ):
                    logo_url += "?ext=.jpg"

            stream_url = f"http://stream.revma.ihrhls.com/zc{station_id}"

            # Fetch live track metadata
            now_playing = ""
            try:
                live_url = f"https://api.iheart.com/api/v2/content/liveStations/{station_id}"
                live_req = urllib.request.Request(
                    live_url, headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(
                    live_req, timeout=1.0, context=ssl_ctx
                ) as live_resp:
                    live_data = json.loads(live_resp.read().decode('utf-8'))
                    hits = live_data.get('hits', [])
                    if hits:
                        artist = hits[0].get('artist', '').strip()
                        title = hits[0].get('title', '').strip()
                        if artist and title:
                            now_playing = f" | {artist} - {title}"
                        elif title:
                            now_playing = f" | {title}"
            except Exception:
                pass

            display_title = f"{name}{now_playing}"

            if logo_url:
                output.append(
                    f'#EXTINF:-1 tvg-logo="{logo_url}",{display_title}'
                )
            else:
                output.append(f'#EXTINF:-1,{display_title}')

            output.append(stream_url)

except Exception as e:
    print(f"[DEBUG ERROR] {e}", file=sys.stderr)

sys.stdout.write("\r\n".join(output) + "\r\n")
sys.stdout.flush()
