"""
HPL 标准库 - random 模块

提供随机数生成功能。
"""

import random as _random
import uuid as _uuid
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


# 随机数生成函数

def random():
    """生成0-1之间的随机浮点数"""
    return _random.random()


def random_int(min_val, max_val):
    """生成指定范围内的随机整数 [min, max]"""
    if not isinstance(min_val, int):
        raise HPLTypeError(f"random_int() requires int min, got {type(min_val).__name__}")
    if not isinstance(max_val, int):
        raise HPLTypeError(f"random_int() requires int max, got {type(max_val).__name__}")
    if min_val > max_val:
        raise HPLValueError(f"random_int() min ({min_val}) must be <= max ({max_val})")
    
    return _random.randint(min_val, max_val)


def random_float(min_val, max_val):
    """生成指定范围内的随机浮点数 [min, max)"""
    if not isinstance(min_val, (int, float)):
        raise HPLTypeError(f"random_float() requires number min, got {type(min_val).__name__}")
    if not isinstance(max_val, (int, float)):
        raise HPLTypeError(f"random_float() requires number max, got {type(max_val).__name__}")
    if min_val > max_val:
        raise HPLValueError(f"random_float() min ({min_val}) must be <= max ({max_val})")
    
    return _random.uniform(min_val, max_val)


def choice(array):
    """从数组中随机选择一个元素"""
    if not isinstance(array, list):
        raise HPLTypeError(f"choice() requires array, got {type(array).__name__}")
    if len(array) == 0:
        raise HPLValueError("choice() requires non-empty array")
    
    return _random.choice(array)


def shuffle(array):
    """随机打乱数组（原地修改）"""
    if not isinstance(array, list):
        raise HPLTypeError(f"shuffle() requires array, got {type(array).__name__}")
    
    _random.shuffle(array)
    return array


def sample(array, count):
    """从数组中无放回抽样指定数量的元素"""
    if not isinstance(array, list):
        raise HPLTypeError(f"sample() requires array, got {type(array).__name__}")
    if not isinstance(count, int):
        raise HPLTypeError(f"sample() requires int count, got {type(count).__name__}")
    if count < 0:
        raise HPLValueError("sample() requires non-negative count")
    if count > len(array):
        raise HPLValueError(f"sample() count ({count}) cannot be greater than array length ({len(array)})")
    
    return _random.sample(array, count)


def seed(value):
    """设置随机种子，用于可重复的随机序列"""
    if not isinstance(value, (int, float, str)):
        raise HPLTypeError(f"seed() requires number or string, got {type(value).__name__}")
    
    if isinstance(value, str):
        # 将字符串转换为整数种子
        value = hash(value) % (2**32)
    
    _random.seed(value)
    return True


def uuid():
    """生成UUID v4（随机UUID）"""
    return str(_uuid.uuid4())


def uuid1():
    """生成UUID v1（基于时间和MAC地址）"""
    return str(_uuid.uuid1())


def uuid3(namespace, name):
    """生成UUID v3（基于MD5哈希）"""
    if not isinstance(name, str):
        raise HPLTypeError(f"uuid3() requires string name, got {type(name).__name__}")
    
    # 预定义的命名空间
    namespaces = {
        'dns': _uuid.NAMESPACE_DNS,
        'url': _uuid.NAMESPACE_URL,
        'oid': _uuid.NAMESPACE_OID,
        'x500': _uuid.NAMESPACE_X500
    }
    
    if isinstance(namespace, str):
        if namespace.lower() in namespaces:
            namespace = namespaces[namespace.lower()]
        else:
            raise HPLValueError(f"uuid3() unknown namespace '{namespace}'. Use: dns, url, oid, x500")
    elif not isinstance(namespace, _uuid.UUID):
        raise HPLTypeError(f"uuid3() requires UUID or string namespace")
    
    return str(_uuid.uuid3(namespace, name))


def uuid5(namespace, name):
    """生成UUID v5（基于SHA1哈希）"""
    if not isinstance(name, str):
        raise HPLTypeError(f"uuid5() requires string name, got {type(name).__name__}")
    
    # 预定义的命名空间
    namespaces = {
        'dns': _uuid.NAMESPACE_DNS,
        'url': _uuid.NAMESPACE_URL,
        'oid': _uuid.NAMESPACE_OID,
        'x500': _uuid.NAMESPACE_X500
    }
    
    if isinstance(namespace, str):
        if namespace.lower() in namespaces:
            namespace = namespaces[namespace.lower()]
        else:
            raise HPLValueError(f"uuid5() unknown namespace '{namespace}'. Use: dns, url, oid, x500")
    elif not isinstance(namespace, _uuid.UUID):
        raise HPLTypeError(f"uuid5() requires UUID or string namespace")
    
    return str(_uuid.uuid5(namespace, name))


def random_bytes(length):
    """生成指定长度的随机字节串"""
    if not isinstance(length, int):
        raise HPLTypeError(f"random_bytes() requires int length, got {type(length).__name__}")
    if length < 0:
        raise HPLValueError("random_bytes() requires non-negative length")
    if length > 65536:  # 限制最大长度
        raise HPLValueError("random_bytes() length cannot exceed 65536")
    
    return _os.urandom(length)


def random_hex(length):
    """生成指定长度的随机十六进制字符串"""
    if not isinstance(length, int):
        raise HPLTypeError(f"random_hex() requires int length, got {type(length).__name__}")
    if length < 0:
        raise HPLValueError("random_hex() requires non-negative length")
    if length > 65536:  # 限制最大长度
        raise HPLValueError("random_hex() length cannot exceed 65536")
    
    return _os.urandom(length).hex()


def random_bool():
    """生成随机布尔值"""
    return _random.choice([True, False])


def gauss(mu=0.0, sigma=1.0):
    """生成符合高斯分布的随机数"""
    if not isinstance(mu, (int, float)):
        raise HPLTypeError(f"gauss() requires number mu, got {type(mu).__name__}")
    if not isinstance(sigma, (int, float)):
        raise HPLTypeError(f"gauss() requires number sigma, got {type(sigma).__name__}")
    if sigma < 0:
        raise HPLValueError("gauss() sigma must be non-negative")
    
    return _random.gauss(mu, sigma)


def triangular(low=0.0, high=1.0, mode=None):
    """生成符合三角分布的随机数"""
    if not isinstance(low, (int, float)):
        raise HPLTypeError(f"triangular() requires number low, got {type(low).__name__}")
    if not isinstance(high, (int, float)):
        raise HPLTypeError(f"triangular() requires number high, got {type(high).__name__}")
    if mode is not None and not isinstance(mode, (int, float)):
        raise HPLTypeError(f"triangular() requires number mode, got {type(mode).__name__}")
    
    return _random.triangular(low, high, mode)


def expovariate(lambd):
    """生成符合指数分布的随机数"""
    if not isinstance(lambd, (int, float)):
        raise HPLTypeError(f"expovariate() requires number lambda, got {type(lambd).__name__}")
    if lambd <= 0:
        raise HPLValueError("expovariate() lambda must be positive")
    
    return _random.expovariate(lambd)


def betavariate(alpha, beta):
    """生成符合Beta分布的随机数"""
    if not isinstance(alpha, (int, float)):
        raise HPLTypeError(f"betavariate() requires number alpha, got {type(alpha).__name__}")
    if not isinstance(beta, (int, float)):
        raise HPLTypeError(f"betavariate() requires number beta, got {type(beta).__name__}")
    if alpha <= 0:
        raise HPLValueError("betavariate() alpha must be positive")
    if beta <= 0:
        raise HPLValueError("betavariate() beta must be positive")
    
    return _random.betavariate(alpha, beta)


def gammavariate(alpha, beta):
    """生成符合Gamma分布的随机数"""
    if not isinstance(alpha, (int, float)):
        raise HPLTypeError(f"gammavariate() requires number alpha, got {type(alpha).__name__}")
    if not isinstance(beta, (int, float)):
        raise HPLTypeError(f"gammavariate() requires number beta, got {type(beta).__name__}")
    if alpha <= 0:
        raise HPLValueError("gammavariate() alpha must be positive")
    if beta <= 0:
        raise HPLValueError("gammavariate() beta must be positive")
    
    return _random.gammavariate(alpha, beta)


def lognormvariate(mu, sigma):
    """生成符合对数正态分布的随机数"""
    if not isinstance(mu, (int, float)):
        raise HPLTypeError(f"lognormvariate() requires number mu, got {type(mu).__name__}")
    if not isinstance(sigma, (int, float)):
        raise HPLTypeError(f"lognormvariate() requires number sigma, got {type(sigma).__name__}")
    if sigma <= 0:
        raise HPLValueError("lognormvariate() sigma must be positive")
    
    return _random.lognormvariate(mu, sigma)


def vonmisesvariate(mu, kappa):
    """生成符合von Mises分布的随机数"""
    if not isinstance(mu, (int, float)):
        raise HPLTypeError(f"vonmisesvariate() requires number mu, got {type(mu).__name__}")
    if not isinstance(kappa, (int, float)):
        raise HPLTypeError(f"vonmisesvariate() requires number kappa, got {type(kappa).__name__}")
    if kappa < 0:
        raise HPLValueError("vonmisesvariate() kappa must be non-negative")
    
    return _random.vonmisesvariate(mu, kappa)


def paretovariate(alpha):
    """生成符合Pareto分布的随机数"""
    if not isinstance(alpha, (int, float)):
        raise HPLTypeError(f"paretovariate() requires number alpha, got {type(alpha).__name__}")
    if alpha <= 0:
        raise HPLValueError("paretovariate() alpha must be positive")
    
    return _random.paretovariate(alpha)


def weibullvariate(alpha, beta):
    """生成符合Weibull分布的随机数"""
    if not isinstance(alpha, (int, float)):
        raise HPLTypeError(f"weibullvariate() requires number alpha, got {type(alpha).__name__}")
    if not isinstance(beta, (int, float)):
        raise HPLTypeError(f"weibullvariate() requires number beta, got {type(beta).__name__}")
    if alpha <= 0:
        raise HPLValueError("weibullvariate() alpha must be positive")
    if beta <= 0:
        raise HPLValueError("weibullvariate() beta must be positive")
    
    return _random.weibullvariate(alpha, beta)


def getstate():
    """获取随机数生成器的当前状态"""
    return _random.getstate()


def setstate(state):
    """恢复随机数生成器的状态"""
    _random.setstate(state)
    return True


# 创建模块实例
module = HPLModule('random', 'Random number generation functions')

# 注册函数
module.register_function('random', random, 0, 'Generate random float in [0, 1)')
module.register_function('random_int', random_int, 2, 'Generate random integer in [min, max]')
module.register_function('random_float', random_float, 2, 'Generate random float in [min, max)')
module.register_function('choice', choice, 1, 'Randomly select element from array')
module.register_function('shuffle', shuffle, 1, 'Shuffle array in place')
module.register_function('sample', sample, 2, 'Sample k elements without replacement')
module.register_function('seed', seed, 1, 'Set random seed for reproducibility')
module.register_function('uuid', uuid, 0, 'Generate UUID v4 (random)')
module.register_function('uuid1', uuid1, 0, 'Generate UUID v1 (time-based)')
module.register_function('uuid3', uuid3, 2, 'Generate UUID v3 (MD5-based)')
module.register_function('uuid5', uuid5, 2, 'Generate UUID v5 (SHA1-based)')
module.register_function('random_bytes', random_bytes, 1, 'Generate random bytes')
module.register_function('random_hex', random_hex, 1, 'Generate random hex string')
module.register_function('random_bool', random_bool, 0, 'Generate random boolean')
module.register_function('gauss', gauss, None, 'Generate Gaussian distributed random (optional mu, sigma)')
module.register_function('triangular', triangular, None, 'Generate triangular distributed random (optional low, high, mode)')
module.register_function('expovariate', expovariate, 1, 'Generate exponentially distributed random')
module.register_function('betavariate', betavariate, 2, 'Generate Beta distributed random')
module.register_function('gammavariate', gammavariate, 2, 'Generate Gamma distributed random')
module.register_function('lognormvariate', lognormvariate, 2, 'Generate log-normal distributed random')
module.register_function('vonmisesvariate', vonmisesvariate, 2, 'Generate von Mises distributed random')
module.register_function('paretovariate', paretovariate, 1, 'Generate Pareto distributed random')
module.register_function('weibullvariate', weibullvariate, 2, 'Generate Weibull distributed random')
module.register_function('getstate', getstate, 0, 'Get random generator state')
module.register_function('setstate', setstate, 1, 'Set random generator state')

