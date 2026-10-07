#!/usr/bin/env -S python3 -u -W ignore
from cgi import FieldStorage
import os
import sys
import json
import ssl
import urllib.parse
import urllib.request

sys.stdout.write("Content-Type: audio/x-scpls; charset=UTF-8\r\n")
sys.stdout.write('Content-Disposition: attachment; filename="iheart.pls"\r\n')
sys.stdout.write("\r\n")  # Blank line terminates HTTP headers
sys.stdout.flush()

# 2. Prevent FieldStorage stdin hang on GET requests
if os.environ.get('REQUEST_METHOD') == 'GET':
    os.environ.pop('CONTENT_LENGTH', None)
    os.environ.pop('CONTENT_TYPE', None)

form = FieldStorage()
q = form.getvalue("q", "")

if not q:
    query_string = os.environ.get('QUERY_STRING', '')
    params = urllib.parse.parse_qs(query_string)
    q = params.get('q', [''])[0]

q = q.strip()
if not q:
    q = "top"

# Construct PLS Body (Line 1 MUST be [playlist])
output = ["[playlist]"]
entries = []

try:
    api_url = f"https://api.iheart.com/api/v1/catalog/searchAll?keywords={urllib.parse.quote(q)}"
    req = urllib.request.Request(
        api_url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    with urllib.request.urlopen(req, timeout=5, context=ssl_ctx) as resp:
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

        for station in stations[:15]:
            if isinstance(station, dict):
                name = station.get('name') or station.get('callLetters') or 'iHeart Station'
                station_id = station.get('id')

                if station_id:
                    stream_url = f"http://stream.revma.ihrhls.com/zc{station_id}"
                    entries.append((name, stream_url))

except Exception as e:
    print(f"[DEBUG ERROR] {e}", file=sys.stderr)

output.append(f"NumberOfEntries={len(entries)}")

for i, (title, stream_url) in enumerate(entries, start=1):
    output.append(f"File{i}={stream_url}")
    output.append(f"Title{i}={title}")
    output.append(f"Length{i}=-1")

output.append("Version=2")

sys.stdout.write("\r\n".join(output) + "\r\n")
sys.stdout.flush()
