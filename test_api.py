import urllib.request
import json
import ssl

url = 'https://openrouter.ai/api/v1/chat/completions'
headers = {
    'Authorization': 'Bearer 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',
    'Content-Type': 'application/json',
    'HTTP-Referer': 'http://localhost'
}
data = {
    'model': 'openai/gpt-oss-120b:free',
    'messages': [{'role': 'user', 'content': 'Hello'}]
}

try:
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, context=ctx) as response:
        print("Success:")
        print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
