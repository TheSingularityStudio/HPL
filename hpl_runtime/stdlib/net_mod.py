"""
HPL 标准库 - net 模块 (网络)

提供HTTP客户端功能，支持GET、POST等请求。
"""

import urllib.request as _urllib_request
import urllib.parse as _urllib_parse
import urllib.error as _urllib_error
import json as _json
import ssl as _ssl

try:
    from hpl_runtime.modules.base import HPLModule
    from hpl_runtime.utils.exceptions import HPLTypeError, HPLValueError, HPLIOError
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from hpl_runtime.modules.base import HPLModule
    from hpl_runtime.utils.exceptions import HPLTypeError, HPLValueError, HPLIOError


def _create_ssl_context(verify=True):
    """创建SSL上下文"""
    if verify:
        return _ssl.create_default_context()
    else:
        # 不验证证书（用于测试）
        context = _ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = _ssl.CERT_NONE
        return context

def _make_request(url, method='GET', data=None, headers=None, timeout=30, verify_ssl=True):
    """执行HTTP请求"""
    if headers is None:
        headers = {}
    
    # 准备数据
    if data is not None:
        if isinstance(data, dict):
            # 自动将字典转为JSON
            data = _json.dumps(data).encode('utf-8')
            headers['Content-Type'] = headers.get('Content-Type', 'application/json')
        elif isinstance(data, str):
            data = data.encode('utf-8')
        elif isinstance(data, bytes):
            pass
        else:
            raise HPLTypeError(f"Request data must be string, dict, or bytes, got {type(data).__name__}")
    
    # 创建请求
    req = _urllib_request.Request(
        url,
        data=data,
        headers=headers,
        method=method
    )
    
    # 执行请求
    try:
        context = _create_ssl_context(verify_ssl)
        with _urllib_request.urlopen(req, timeout=timeout, context=context) as response:
            body = response.read()
            return {
                'status': response.status,
                'reason': response.reason,
                'headers': dict(response.headers),
                'body': body.decode('utf-8'),
                'url': response.url
            }
    except _urllib_error.HTTPError as e:
        # HTTP错误（4xx, 5xx）
        body = e.read().decode('utf-8') if e.read() else ''
        return {
            'status': e.code,
            'reason': e.reason,
            'headers': dict(e.headers),
            'body': body,
            'url': e.url,
            'error': f"HTTP {e.code}: {e.reason}"
        }
    except _urllib_error.URLError as e:
        raise HPLIOError(f"Request failed: {e.reason}", operation=f"{method} {url}")
    except Exception as e:
        raise HPLIOError(f"Request error: {e}", operation=f"{method} {url}")

def get(url, headers=None, timeout=30, verify_ssl=True):
    """
    发送HTTP GET请求
    
    返回响应对象：{status, reason, headers, body, url}
    """
    if not isinstance(url, str):
        raise HPLTypeError(f"get() requires string url, got {type(url).__name__}")
    if headers is not None and not isinstance(headers, dict):
        raise HPLTypeError(f"get() requires dict headers, got {type(headers).__name__}")
    if not isinstance(timeout, (int, float)):
        raise HPLTypeError(f"get() requires number timeout, got {type(timeout).__name__}")
    
    return _make_request(url, 'GET', None, headers, timeout, verify_ssl)

def post(url, data=None, headers=None, timeout=30, verify_ssl=True):
    """
    发送HTTP POST请求
    
    data可以是字符串或字典（自动转为JSON）
    返回响应对象：{status, reason, headers, body, url}
    """
    if not isinstance(url, str):
        raise HPLTypeError(f"post() requires string url, got {type(url).__name__}")
    if headers is not None and not isinstance(headers, dict):
        raise HPLTypeError(f"post() requires dict headers, got {type(headers).__name__}")
    if not isinstance(timeout, (int, float)):
        raise HPLTypeError(f"post() requires number timeout, got {type(timeout).__name__}")
    
    return _make_request(url, 'POST', data, headers, timeout, verify_ssl)

def put(url, data=None, headers=None, timeout=30, verify_ssl=True):
    """
    发送HTTP PUT请求
    
    返回响应对象：{status, reason, headers, body, url}
    """
    if not isinstance(url, str):
        raise HPLTypeError(f"put() requires string url, got {type(url).__name__}")
    if headers is not None and not isinstance(headers, dict):
        raise HPLTypeError(f"put() requires dict headers, got {type(headers).__name__}")
    if not isinstance(timeout, (int, float)):
        raise HPLTypeError(f"put() requires number timeout, got {type(timeout).__name__}")
    
    return _make_request(url, 'PUT', data, headers, timeout, verify_ssl)

def delete(url, headers=None, timeout=30, verify_ssl=True):
    """
    发送HTTP DELETE请求
    
    返回响应对象：{status, reason, headers, body, url}
    """
    if not isinstance(url, str):
        raise HPLTypeError(f"delete() requires string url, got {type(url).__name__}")
    if headers is not None and not isinstance(headers, dict):
        raise HPLTypeError(f"delete() requires dict headers, got {type(headers).__name__}")
    if not isinstance(timeout, (int, float)):
        raise HPLTypeError(f"delete() requires number timeout, got {type(timeout).__name__}")
    
    return _make_request(url, 'DELETE', None, headers, timeout, verify_ssl)

def head(url, headers=None, timeout=30, verify_ssl=True):
    """
    发送HTTP HEAD请求
    
    返回响应对象（无body）：{status, reason, headers, url}
    """
    if not isinstance(url, str):
        raise HPLTypeError(f"head() requires string url, got {type(url).__name__}")
    if headers is not None and not isinstance(headers, dict):
        raise HPLTypeError(f"head() requires dict headers, got {type(headers).__name__}")
    if not isinstance(timeout, (int, float)):
        raise HPLTypeError(f"head() requires number timeout, got {type(timeout).__name__}")
    
    result = _make_request(url, 'HEAD', None, headers, timeout, verify_ssl)
    # HEAD请求通常没有body
    result['body'] = ''
    return result

def request(method, url, data=None, headers=None, timeout=30, verify_ssl=True):
    """
    发送任意HTTP请求
    
    method: GET, POST, PUT, DELETE, HEAD, PATCH, OPTIONS等
    返回响应对象
    """
    if not isinstance(method, str):
        raise HPLTypeError(f"request() requires string method, got {type(method).__name__}")
    if not isinstance(url, str):
        raise HPLTypeError(f"request() requires string url, got {type(url).__name__}")
    
    method = method.upper()
    valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'PATCH', 'OPTIONS', 'TRACE', 'CONNECT']
    if method not in valid_methods:
        raise HPLValueError(f"Invalid HTTP method: {method}. Valid: {', '.join(valid_methods)}")
    
    return _make_request(url, method, data, headers, timeout, verify_ssl)

def encode_url(params):
    """
    URL编码参数字典
    
    返回编码后的查询字符串
    """
    if not isinstance(params, dict):
        raise HPLTypeError(f"encode_url() requires dict, got {type(params).__name__}")
    
    return _urllib_parse.urlencode(params)

def decode_url(query_string):
    """
    解码URL查询字符串
    
    返回参数字典
    """
    if not isinstance(query_string, str):
        raise HPLTypeError(f"decode_url() requires string, got {type(query_string).__name__}")
    
    return dict(_urllib_parse.parse_qsl(query_string))

def parse_url(url):
    """
    解析URL
    
    返回URL组件：{scheme, netloc, path, params, query, fragment, username, password, hostname, port}
    """
    if not isinstance(url, str):
        raise HPLTypeError(f"parse_url() requires string, got {type(url).__name__}")
    
    parsed = _urllib_parse.urlparse(url)
    return {
        'scheme': parsed.scheme,
        'netloc': parsed.netloc,
        'path': parsed.path,
        'params': parsed.params,
        'query': parsed.query,
        'fragment': parsed.fragment,
        'username': parsed.username,
        'password': parsed.password,
        'hostname': parsed.hostname,
        'port': parsed.port
    }

def build_url(base, params=None):
    """
    构建完整URL
    
    base: 基础URL
    params: 可选的查询参数字典
    """
    if not isinstance(base, str):
        raise HPLTypeError(f"build_url() requires string base, got {type(base).__name__}")
    
    if params:
        if not isinstance(params, dict):
            raise HPLTypeError(f"build_url() requires dict params, got {type(params).__name__}")
        query = encode_url(params)
        separator = '&' if '?' in base else '?'
        return f"{base}{separator}{query}"
    
    return base

def is_success(status_code):
    """
    检查HTTP状态码是否表示成功 (2xx)
    
    返回布尔值
    """
    if not isinstance(status_code, int):
        raise HPLTypeError(f"is_success() requires int, got {type(status_code).__name__}")
    
    return 200 <= status_code < 300

def is_redirect(status_code):
    """
    检查HTTP状态码是否表示重定向 (3xx)
    
    返回布尔值
    """
    if not isinstance(status_code, int):
        raise HPLTypeError(f"is_redirect() requires int, got {type(status_code).__name__}")
    
    return 300 <= status_code < 400

def is_client_error(status_code):
    """
    检查HTTP状态码是否表示客户端错误 (4xx)
    
    返回布尔值
    """
    if not isinstance(status_code, int):
        raise HPLTypeError(f"is_client_error() requires int, got {type(status_code).__name__}")
    
    return 400 <= status_code < 500

def is_server_error(status_code):
    """
    检查HTTP状态码是否表示服务器错误 (5xx)
    
    返回布尔值
    """
    if not isinstance(status_code, int):
        raise HPLTypeError(f"is_server_error() requires int, got {type(status_code).__name__}")
    
    return 500 <= status_code < 600

# 创建模块实例
module = HPLModule('net', 'HTTP networking operations')

# 注册函数
module.register_function('get', get, None, 'HTTP GET request')
module.register_function('post', post, None, 'HTTP POST request')
module.register_function('put', put, None, 'HTTP PUT request')
module.register_function('delete', delete, None, 'HTTP DELETE request')
module.register_function('head', head, None, 'HTTP HEAD request')
module.register_function('request', request, None, 'Generic HTTP request')

# URL处理函数
module.register_function('encode_url', encode_url, 1, 'URL encode parameters')
module.register_function('decode_url', decode_url, 1, 'URL decode query string')
module.register_function('parse_url', parse_url, 1, 'Parse URL components')
module.register_function('build_url', build_url, None, 'Build URL with parameters')

# HTTP状态码检查
module.register_function('is_success', is_success, 1, 'Check if 2xx status')
module.register_function('is_redirect', is_redirect, 1, 'Check if 3xx status')
module.register_function('is_client_error', is_client_error, 1, 'Check if 4xx status')
module.register_function('is_server_error', is_server_error, 1, 'Check if 5xx status')

# 注册常用HTTP状态码常量
HTTP_STATUS_CODES = {
    'OK': 200,
    'CREATED': 201,
    'ACCEPTED': 202,
    'NO_CONTENT': 204,
    'MOVED_PERMANENTLY': 301,
    'FOUND': 302,
    'NOT_MODIFIED': 304,
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'FORBIDDEN': 403,
    'NOT_FOUND': 404,
    'METHOD_NOT_ALLOWED': 405,
    'INTERNAL_ERROR': 500,
    'NOT_IMPLEMENTED': 501,
    'BAD_GATEWAY': 502,
    'SERVICE_UNAVAILABLE': 503,
}

for name, code in HTTP_STATUS_CODES.items():
    module.register_constant(f'STATUS_{name}', code, f'HTTP status code {code}')
