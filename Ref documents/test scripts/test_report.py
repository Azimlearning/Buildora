import urllib.request, json, sys

url = "http://localhost:8000/api/reports/test123/generate"
payload = json.dumps({
    "project": {
        "name": "KL Tower Renovation",
        "contractor": "Apex Construction Builders",
        "cidb_grade": "G7",
        "health_score": 88,
        "description": "Modernization of observation deck facilities."
    }
}).encode()

req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        print("Generate response:", data)
except Exception as e:
    print("Error:", e)
    if hasattr(e, 'read'):
        print("Detail:", e.read().decode())

# Try download
url2 = "http://localhost:8000/api/reports/test123/download/pdf"
req2 = urllib.request.Request(url2)
try:
    with urllib.request.urlopen(req2) as resp:
        content = resp.read()
        print(f"PDF downloaded OK, size={len(content)} bytes")
except Exception as e:
    print("Download error:", e)
    if hasattr(e, 'read'):
        print("Detail:", e.read().decode())
