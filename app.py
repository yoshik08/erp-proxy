from flask import Flask, request, Response
import requests

app = Flask(__name__)
ERP_BASE = "https://newerp.kluniversity.in"
TIMEOUT = 25

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
def proxy(path):
    url = f"{ERP_BASE}/{path}"
    # Forward query string
    if request.query_string:
        url += f"?{request.query_string.decode()}"
    
    # Forward headers (excluding host)
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
        # Build response
        excluded = ('content-encoding', 'content-length', 'transfer-encoding', 'connection')
        resp_headers = [(k, v) for k, v in resp.headers.items() if k.lower() not in excluded]
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
