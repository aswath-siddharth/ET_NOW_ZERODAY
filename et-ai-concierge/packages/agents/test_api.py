import urllib.request
import json
import traceback

data = json.dumps({"user_id": "test_user_123", "message": ""}).encode('utf-8')
req = urllib.request.Request(
    'http://localhost:8001/api/chat/xray',
    data=data,
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    with urllib.request.urlopen(req) as response:
        print("Success:", response.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}:")
    print(e.read().decode())
except Exception as e:
    print("Other Error:")
    traceback.print_exc()
