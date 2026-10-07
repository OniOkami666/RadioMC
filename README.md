# RadioMC - How it works

Essentially, it is a Python CGI (Common Gateway Interface) file converting iHeartRadio search results into a .pls file (playlist file).  It allows wiimc to stream iHeartRadio channels directly to the console.

# Diagram

```

[ WiiMC ]
   │
   │  1. HTTP GET (?q=)
   ▼
[ Server (CGI Script) ]
   │
   │  2. Search Query API Call
   ▼
[ iHeartRadio API ]
   │
   │  3. Returns Station Data & IDs
   ▼
[ Server (CGI Script) ]
   │
   │  4. Converts IDs to Direct Streams & Formats PLS
   ▼
[ WiiMC ] (Loads iheart.pls and plays streams directly)

```
