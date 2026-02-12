"""
HPL 标准库 - crypto 模块

提供加密哈希、编码功能。
"""

import hashlib as _hashlib
import hmac as _hmac
import base64 as _base64
import urllib.parse as _urllib_parse
import secrets as _secrets
import os as _os

try:
    from hpl_runtime.modules.base import HPLModule
    from hpl_runtime.utils.exceptions import HPLTypeError, HPLValueError
except ImportError:
    try:
        from hpl_runtime.modules.base import HPLModule
        from hpl_runtime.utils.exceptions import HPLTypeError, HPLValueError
    except ImportError:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from hpl_runtime.modules.base import HPLModule
        from hpl_runtime.utils.exceptions import HPLTypeError, HPLValueError


# 哈希函数

def md5(data):
    """计算MD5哈希（32位十六进制字符串）"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    elif not isinstance(data, bytes):
        raise HPLTypeError(f"md5() requires string or bytes, got {type(data).__name__}")
    
    return _hashlib.md5(data).hexdigest()


def sha1(data):
    """计算SHA1哈希（40位十六进制字符串）"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    elif not isinstance(data, bytes):
        raise HPLTypeError(f"sha1() requires string or bytes, got {type(data).__name__}")
    
    return _hashlib.sha1(data).hexdigest()


def sha256(data):
    """计算SHA256哈希（64位十六进制字符串）"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    elif not isinstance(data, bytes):
        raise HPLTypeError(f"sha256() requires string or bytes, got {type(data).__name__}")
    
    return _hashlib.sha256(data).hexdigest()


def sha512(data):
    """计算SHA512哈希（128位十六进制字符串）"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    elif not isinstance(data, bytes):
        raise HPLTypeError(f"sha512() requires string or bytes, got {type(data).__name__}")
    
    return _hashlib.sha512(data).hexdigest()


def sha3_256(data):
    """计算SHA3-256哈希（如果可用）"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    elif not isinstance(data, bytes):
        raise HPLTypeError(f"sha3_256() requires string or bytes, got {type(data).__name__}")
    
    try:
        return _hashlib.sha3_256(data).hexdigest()
    except AttributeError:
        raise HPLValueError("sha3_256() not available in this Python version")


def sha3_512(data):
    """计算SHA3-512哈希（如果可用）"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    elif not isinstance(data, bytes):
        raise HPLTypeError(f"sha3_512() requires string or bytes, got {type(data).__name__}")
    
    try:
        return _hashlib.sha3_512(data).hexdigest()
    except AttributeError:
        raise HPLValueError("sha3_512() not available in this Python version")


def blake2b(data, digest_size=64):
    """计算BLAKE2b哈希"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    elif not isinstance(data, bytes):
        raise HPLTypeError(f"blake2b() requires string or bytes, got {type(data).__name__}")
    if not isinstance(digest_size, int):
        raise HPLTypeError(f"blake2b() requires int digest_size, got {type(digest_size).__name__}")
    
    try:
        return _hashlib.blake2b(data, digest_size=digest_size).hexdigest()
    except AttributeError:
        raise HPLValueError("blake2b() not available in this Python version")


def blake2s(data, digest_size=32):
    """计算BLAKE2s哈希"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    elif not isinstance(data, bytes):
        raise HPLTypeError(f"blake2s() requires string or bytes, got {type(data).__name__}")
    if not isinstance(digest_size, int):
        raise HPLTypeError(f"blake2s() requires int digest_size, got {type(digest_size).__name__}")
    
    try:
        return _hashlib.blake2s(data, digest_size=digest_size).hexdigest()
    except AttributeError:
        raise HPLValueError("blake2s() not available in this Python version")


def hash(data, algorithm='sha256'):
    """使用指定算法计算哈希"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    elif not isinstance(data, bytes):
        raise HPLTypeError(f"hash() requires string or bytes, got {type(data).__name__}")
    if not isinstance(algorithm, str):
        raise HPLTypeError(f"hash() requires string algorithm, got {type(algorithm).__name__}")
    
    algorithm = algorithm.lower().replace('-', '_')
    
    # 支持的算法映射
    algorithms = {
        'md5': 'md5',
        'sha1': 'sha1',
        'sha224': 'sha224',
        'sha256': 'sha256',
        'sha384': 'sha384',
        'sha512': 'sha512',
        'sha3_256': 'sha3_256',
        'sha3_512': 'sha3_512',
        'blake2b': 'blake2b',
        'blake2s': 'blake2s',
    }
    
    if algorithm not in algorithms:
        raise HPLValueError(f"hash() unknown algorithm '{algorithm}'. Supported: {', '.join(algorithms.keys())}")
    
    try:
        hasher = _hashlib.new(algorithms[algorithm])
        hasher.update(data)
        return hasher.hexdigest()
    except ValueError as e:
        raise HPLValueError(f"hash() algorithm not available: {e}")


def hmac(data, key, algorithm='sha256'):
    """计算HMAC签名"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    elif not isinstance(data, bytes):
        raise HPLTypeError(f"hmac() requires string or bytes data, got {type(data).__name__}")
    
    if isinstance(key, str):
        key = key.encode('utf-8')
    elif not isinstance(key, bytes):
        raise HPLTypeError(f"hmac() requires string or bytes key, got {type(key).__name__}")
    
    if not isinstance(algorithm, str):
        raise HPLTypeError(f"hmac() requires string algorithm, got {type(algorithm).__name__}")
    
    algorithm = algorithm.lower().replace('-', '_')
    
    # 支持的HMAC算法
    algorithms = {
        'md5': _hashlib.md5,
        'sha1': _hashlib.sha1,
        'sha224': _hashlib.sha224,
        'sha256': _hashlib.sha256,
        'sha384': _hashlib.sha384,
        'sha512': _hashlib.sha512,
    }
    
    if algorithm not in algorithms:
        raise HPLValueError(f"hmac() unknown algorithm '{algorithm}'. Supported: {', '.join(algorithms.keys())}")
    
    return _hmac.new(key, data, algorithms[algorithm]).hexdigest()


# 编码函数

def base64_encode(data):
    """Base64编码"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    elif not isinstance(data, bytes):
        raise HPLTypeError(f"base64_encode() requires string or bytes, got {type(data).__name__}")
    
    return _base64.b64encode(data).decode('ascii')


def base64_decode(data):
    """Base64解码"""
    if not isinstance(data, str):
        raise HPLTypeError(f"base64_decode() requires string, got {type(data).__name__}")
    
    try:
        return _base64.b64decode(data).decode('utf-8')
    except UnicodeDecodeError:
        # 如果无法解码为UTF-8，返回原始bytes
        return _base64.b64decode(data)


def base64_urlsafe_encode(data):
    """URL安全的Base64编码"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    elif not isinstance(data, bytes):
        raise HPLTypeError(f"base64_urlsafe_encode() requires string or bytes, got {type(data).__name__}")
    
    return _base64.urlsafe_b64encode(data).decode('ascii')


def base64_urlsafe_decode(data):
    """URL安全的Base64解码"""
    if not isinstance(data, str):
        raise HPLTypeError(f"base64_urlsafe_decode() requires string, got {type(data).__name__}")
    
    try:
        return _base64.urlsafe_b64decode(data).decode('utf-8')
    except UnicodeDecodeError:
        return _base64.urlsafe_b64decode(data)


def url_encode(data):
    """URL编码"""
    if not isinstance(data, str):
        raise HPLTypeError(f"url_encode() requires string, got {type(data).__name__}")
    
    return _urllib_parse.quote(data, safe='')


def url_decode(data):
    """URL解码"""
    if not isinstance(data, str):
        raise HPLTypeError(f"url_decode() requires string, got {type(data).__name__}")
    
    return _urllib_parse.unquote(data)


def url_encode_plus(data):
    """URL编码（空格转为+）"""
    if not isinstance(data, str):
        raise HPLTypeError(f"url_encode_plus() requires string, got {type(data).__name__}")
    
    return _urllib_parse.quote_plus(data)


def url_decode_plus(data):
    """URL解码（+转为空格）"""
    if not isinstance(data, str):
        raise HPLTypeError(f"url_decode_plus() requires string, got {type(data).__name__}")
    
    return _urllib_parse.unquote_plus(data)


# 安全随机数生成

def secure_random_bytes(length):
    """生成加密安全的随机字节"""
    if not isinstance(length, int):
        raise HPLTypeError(f"secure_random_bytes() requires int length, got {type(length).__name__}")
    if length < 0:
        raise HPLValueError("secure_random_bytes() requires non-negative length")
    if length > 65536:
        raise HPLValueError("secure_random_bytes() length cannot exceed 65536")
    
    return _secrets.token_bytes(length)


def secure_random_hex(length):
    """生成加密安全的随机十六进制字符串"""
    if not isinstance(length, int):
        raise HPLTypeError(f"secure_random_hex() requires int length, got {type(length).__name__}")
    if length < 0:
        raise HPLValueError("secure_random_hex() requires non-negative length")
    if length > 65536:
        raise HPLValueError("secure_random_hex() length cannot exceed 65536")
    
    return _secrets.token_hex(length)


def secure_random_urlsafe(length):
    """生成URL安全的随机字符串"""
    if not isinstance(length, int):
        raise HPLTypeError(f"secure_random_urlsafe() requires int length, got {type(length).__name__}")
    if length < 0:
        raise HPLValueError("secure_random_urlsafe() requires non-negative length")
    if length > 65536:
        raise HPLValueError("secure_random_urlsafe() length cannot exceed 65536")
    
    return _secrets.token_urlsafe(length)


def secure_choice(sequence):
    """从序列中安全地随机选择一个元素"""
    if not isinstance(sequence, (list, str, bytes)):
        raise HPLTypeError(f"secure_choice() requires sequence, got {type(sequence).__name__}")
    if len(sequence) == 0:
        raise HPLValueError("secure_choice() requires non-empty sequence")
    
    return _secrets.choice(sequence)


def compare_digest(a, b):
    """安全地比较两个字符串（防时序攻击）"""
    if isinstance(a, str):
        a = a.encode('utf-8')
    elif not isinstance(a, bytes):
        raise HPLTypeError(f"compare_digest() requires string or bytes, got {type(a).__name__}")
    
    if isinstance(b, str):
        b = b.encode('utf-8')
    elif not isinstance(b, bytes):
        raise HPLTypeError(f"compare_digest() requires string or bytes, got {type(b).__name__}")
    
    return _hmac.compare_digest(a, b)


# 密码学工具

def pbkdf2_hmac(password, salt, iterations=100000, dklen=None, hash_name='sha256'):
    """PBKDF2密钥派生"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    elif not isinstance(password, bytes):
        raise HPLTypeError(f"pbkdf2_hmac() requires string or bytes password")
    
    if isinstance(salt, str):
        salt = salt.encode('utf-8')
    elif not isinstance(salt, bytes):
        raise HPLTypeError(f"pbkdf2_hmac() requires string or bytes salt")
    
    if not isinstance(iterations, int):
        raise HPLTypeError(f"pbkdf2_hmac() requires int iterations")
    if iterations < 1:
        raise HPLValueError("pbkdf2_hmac() iterations must be positive")
    
    if dklen is not None and not isinstance(dklen, int):
        raise HPLTypeError(f"pbkdf2_hmac() requires int dklen")
    
    if not isinstance(hash_name, str):
        raise HPLTypeError(f"pbkdf2_hmac() requires string hash_name")
    
    try:
        result = _hashlib.pbkdf2_hmac(hash_name, password, salt, iterations, dklen)
        return result.hex()
    except ValueError as e:
        raise HPLValueError(f"pbkdf2_hmac() error: {e}")


def scrypt(password, salt, n=2**14, r=8, p=1, dklen=32):
    """scrypt密钥派生（如果可用）"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    elif not isinstance(password, bytes):
        raise HPLTypeError(f"scrypt() requires string or bytes password")
    
    if isinstance(salt, str):
        salt = salt.encode('utf-8')
    elif not isinstance(salt, bytes):
        raise HPLTypeError(f"scrypt() requires string or bytes salt")
    
    try:
        result = _hashlib.scrypt(password, salt, n, r, p, dklen)
        return result.hex()
    except AttributeError:
        raise HPLValueError("scrypt() not available in this Python version")


# 创建模块实例
module = HPLModule('crypto', 'Cryptographic and encoding functions')

# 注册哈希函数
module.register_function('md5', md5, 1, 'Calculate MD5 hash')
module.register_function('sha1', sha1, 1, 'Calculate SHA1 hash')
module.register_function('sha256', sha256, 1, 'Calculate SHA256 hash')
module.register_function('sha512', sha512, 1, 'Calculate SHA512 hash')
module.register_function('sha3_256', sha3_256, 1, 'Calculate SHA3-256 hash')
module.register_function('sha3_512', sha3_512, 1, 'Calculate SHA3-512 hash')
module.register_function('blake2b', blake2b, None, 'Calculate BLAKE2b hash (optional digest_size)')
module.register_function('blake2s', blake2s, None, 'Calculate BLAKE2s hash (optional digest_size)')
module.register_function('hash', hash, None, 'Calculate hash with specified algorithm')
module.register_function('hmac', hmac, None, 'Calculate HMAC signature (optional algorithm)')

# 注册编码函数
module.register_function('base64_encode', base64_encode, 1, 'Base64 encode')
module.register_function('base64_decode', base64_decode, 1, 'Base64 decode')
module.register_function('base64_urlsafe_encode', base64_urlsafe_encode, 1, 'URL-safe Base64 encode')
module.register_function('base64_urlsafe_decode', base64_urlsafe_decode, 1, 'URL-safe Base64 decode')
module.register_function('url_encode', url_encode, 1, 'URL encode')
module.register_function('url_decode', url_decode, 1, 'URL decode')
module.register_function('url_encode_plus', url_encode_plus, 1, 'URL encode (plus for space)')
module.register_function('url_decode_plus', url_decode_plus, 1, 'URL decode (plus to space)')

# 注册安全随机数函数
module.register_function('secure_random_bytes', secure_random_bytes, 1, 'Generate cryptographically secure random bytes')
module.register_function('secure_random_hex', secure_random_hex, 1, 'Generate cryptographically secure random hex string')
module.register_function('secure_random_urlsafe', secure_random_urlsafe, 1, 'Generate URL-safe secure random string')
module.register_function('secure_choice', secure_choice, 1, 'Securely choose random element from sequence')
module.register_function('compare_digest', compare_digest, 2, 'Securely compare two strings (timing attack resistant)')

# 注册密钥派生函数
module.register_function('pbkdf2_hmac', pbkdf2_hmac, None, 'PBKDF2 key derivation (optional iterations, dklen, hash_name)')
module.register_function('scrypt', scrypt, None, 'scrypt key derivation (optional n, r, p, dklen)')

