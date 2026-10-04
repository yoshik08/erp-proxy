from flask import Flask, request, Response
import requests
from urllib.parse import urlparse, urlunparse

app = Flask(__name__)
ERP_BASE = "https://newerp.kluniversity.in"
TIMEOUT = 25

def rewrite_location(location, proxy_base):
    """Rewrite ERP redirect URLs to go through the proxy."""
    if not location:
        return location
    # If it's a relative URL, leave it (will be resolved against proxy)
    if location.startswith('/'):
        return location
    # If it's the ERP URL, rewrite to proxy URL
    if location.startswith(ERP_BASE):
        return proxy_base + location[len(ERP_BASE):]
    return location

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
def proxy(path):
    url = f"{ERP_BASE}/{path}"
    if request.query_string:
        url += f"?{request.query_string.decode()}"
    
    headers = {k: v for k, v in request.headers if k.lower() not in ('host', 'content-length')}
    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
    
    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=TIMEOUT
        )
        excluded = ('content-encoding', 'content-length', 'transfer-encoding', 'connection')
        resp_headers = []
        proxy_base = request.host_url.rstrip('/')
        for k, v in resp.headers.items():
            if k.lower() in excluded:
                continue
            if k.lower() == 'location':
                v = rewrite_location(v, proxy_base)
            resp_headers.append((k, v))
        return Response(resp.content, status=resp.status_code, headers=resp_headers)
    except requests.exceptions.Timeout:
        return Response('ERP timeout', status=504)
    except Exception as e:
        return Response(f'Proxy error: {str(e)}', status=502)

@app.route('/health')
def health():
    return {'ok': True}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
