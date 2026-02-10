"""
HPL 标准库 - time 模块

提供日期时间处理功能。
"""

import time as _time
import datetime as _datetime

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





def now():
    """获取当前时间戳（秒）"""
    return _time.time()


def now_ms():
    """获取当前时间戳（毫秒）"""
    return int(_time.time() * 1000)


def sleep(seconds):
    """休眠指定秒数"""
    if not isinstance(seconds, (int, float)):
        raise HPLTypeError(f"sleep() requires number, got {type(seconds).__name__}")
    if seconds < 0:
        raise HPLValueError("sleep() requires non-negative number")

    
    _time.sleep(seconds)
    return True


def sleep_ms(milliseconds):
    """休眠指定毫秒数"""
    if not isinstance(milliseconds, (int, float)):
        raise HPLTypeError(f"sleep_ms() requires number, got {type(milliseconds).__name__}")
    if milliseconds < 0:
        raise HPLValueError("sleep_ms() requires non-negative number")

    
    _time.sleep(milliseconds / 1000.0)
    return True


def format_time(timestamp=None, format_str="%Y-%m-%d %H:%M:%S"):
    """格式化时间"""
    if timestamp is None:
        dt = _datetime.datetime.now()
    else:
        if not isinstance(timestamp, (int, float)):
            raise HPLTypeError(f"format_time() requires number for timestamp, got {type(timestamp).__name__}")
        dt = _datetime.datetime.fromtimestamp(timestamp)
    
    if not isinstance(format_str, str):
        raise HPLTypeError(f"format_time() requires string for format, got {type(format_str).__name__}")
    
    return dt.strftime(format_str)



def parse_time(time_str, format_str="%Y-%m-%d %H:%M:%S"):
    """解析时间字符串"""
    if not isinstance(time_str, str):
        raise HPLTypeError(f"parse_time() requires string for time, got {type(time_str).__name__}")
    if not isinstance(format_str, str):
        raise HPLTypeError(f"parse_time() requires string for format, got {type(format_str).__name__}")
    
    try:
        dt = _datetime.datetime.strptime(time_str, format_str)
        return dt.timestamp()
    except ValueError as e:
        raise HPLValueError(f"Cannot parse time: {e}")



def get_year(timestamp=None):
    """获取年份"""
    if timestamp is None:
        return _datetime.datetime.now().year
    if not isinstance(timestamp, (int, float)):
        raise HPLTypeError(f"get_year() requires number, got {type(timestamp).__name__}")

    return _datetime.datetime.fromtimestamp(timestamp).year


def get_month(timestamp=None):
    """获取月份 (1-12)"""
    if timestamp is None:
        return _datetime.datetime.now().month
    if not isinstance(timestamp, (int, float)):
        raise HPLTypeError(f"get_month() requires number, got {type(timestamp).__name__}")

    return _datetime.datetime.fromtimestamp(timestamp).month


def get_day(timestamp=None):
    """获取日期 (1-31)"""
    if timestamp is None:
        return _datetime.datetime.now().day
    if not isinstance(timestamp, (int, float)):
        raise HPLTypeError(f"get_day() requires number, got {type(timestamp).__name__}")

    return _datetime.datetime.fromtimestamp(timestamp).day


def get_hour(timestamp=None):
    """获取小时 (0-23)"""
    if timestamp is None:
        return _datetime.datetime.now().hour
    if not isinstance(timestamp, (int, float)):
        raise HPLTypeError(f"get_hour() requires number, got {type(timestamp).__name__}")

    return _datetime.datetime.fromtimestamp(timestamp).hour


def get_minute(timestamp=None):
    """获取分钟 (0-59)"""
    if timestamp is None:
        return _datetime.datetime.now().minute
    if not isinstance(timestamp, (int, float)):
        raise HPLTypeError(f"get_minute() requires number, got {type(timestamp).__name__}")

    return _datetime.datetime.fromtimestamp(timestamp).minute


def get_second(timestamp=None):
    """获取秒 (0-59)"""
    if timestamp is None:
        return _datetime.datetime.now().second
    if not isinstance(timestamp, (int, float)):
        raise HPLTypeError(f"get_second() requires number, got {type(timestamp).__name__}")

    return _datetime.datetime.fromtimestamp(timestamp).second


def get_weekday(timestamp=None):
    """获取星期几 (0=周一, 6=周日)"""
    if timestamp is None:
        return _datetime.datetime.now().weekday()
    if not isinstance(timestamp, (int, float)):
        raise HPLTypeError(f"get_weekday() requires number, got {type(timestamp).__name__}")

    return _datetime.datetime.fromtimestamp(timestamp).weekday()


def get_iso_date(timestamp=None):
    """获取 ISO 格式日期"""
    if timestamp is None:
        return _datetime.datetime.now().date().isoformat()
    if not isinstance(timestamp, (int, float)):
        raise HPLTypeError(f"get_iso_date() requires number, got {type(timestamp).__name__}")

    return _datetime.datetime.fromtimestamp(timestamp).date().isoformat()


def get_iso_time(timestamp=None):
    """获取 ISO 格式时间"""
    if timestamp is None:
        return _datetime.datetime.now().time().isoformat()
    if not isinstance(timestamp, (int, float)):
        raise HPLTypeError(f"get_iso_time() requires number, got {type(timestamp).__name__}")

    return _datetime.datetime.fromtimestamp(timestamp).time().isoformat()


def add_days(timestamp, days):
    """添加天数"""
    if not isinstance(timestamp, (int, float)):
        raise HPLTypeError(f"add_days() requires number for timestamp, got {type(timestamp).__name__}")
    if not isinstance(days, (int, float)):
        raise HPLTypeError(f"add_days() requires number for days, got {type(days).__name__}")

    
    dt = _datetime.datetime.fromtimestamp(timestamp)
    new_dt = dt + _datetime.timedelta(days=days)
    return new_dt.timestamp()


def diff_days(timestamp1, timestamp2):
    """计算两个时间戳相差的天数"""
    if not isinstance(timestamp1, (int, float)):
        raise HPLTypeError(f"diff_days() requires number for timestamp1, got {type(timestamp1).__name__}")
    if not isinstance(timestamp2, (int, float)):
        raise HPLTypeError(f"diff_days() requires number for timestamp2, got {type(timestamp2).__name__}")

    
    dt1 = _datetime.datetime.fromtimestamp(timestamp1)
    dt2 = _datetime.datetime.fromtimestamp(timestamp2)
    diff = dt2 - dt1
    return diff.days


def utc_now():
    """获取 UTC 时间戳"""
    return _datetime.datetime.utcnow().timestamp()


def local_timezone():
    """获取本地时区偏移（小时）"""
    if _time.daylight:
        return -_time.altzone / 3600
    else:
        return -_time.timezone / 3600


# 创建模块实例
module = HPLModule('time', 'Date and time functions')

# 注册函数
module.register_function('now', now, 0, 'Get current timestamp in seconds')
module.register_function('now_ms', now_ms, 0, 'Get current timestamp in milliseconds')
module.register_function('sleep', sleep, 1, 'Sleep for specified seconds')
module.register_function('sleep_ms', sleep_ms, 1, 'Sleep for specified milliseconds')
module.register_function('format', format_time, None, 'Format timestamp (optional format)')
module.register_function('parse', parse_time, None, 'Parse time string (optional format)')
module.register_function('get_year', get_year, None, 'Get year from timestamp')
module.register_function('get_month', get_month, None, 'Get month from timestamp (1-12)')
module.register_function('get_day', get_day, None, 'Get day from timestamp (1-31)')
module.register_function('get_hour', get_hour, None, 'Get hour from timestamp (0-23)')
module.register_function('get_minute', get_minute, None, 'Get minute from timestamp (0-59)')
module.register_function('get_second', get_second, None, 'Get second from timestamp (0-59)')
module.register_function('get_weekday', get_weekday, None, 'Get weekday from timestamp (0=Mon, 6=Sun)')
module.register_function('get_iso_date', get_iso_date, None, 'Get ISO date string')
module.register_function('get_iso_time', get_iso_time, None, 'Get ISO time string')
module.register_function('add_days', add_days, 2, 'Add days to timestamp')
module.register_function('diff_days', diff_days, 2, 'Calculate difference in days')
module.register_function('utc_now', utc_now, 0, 'Get UTC timestamp')
module.register_function('local_timezone', local_timezone, 0, 'Get local timezone offset in hours')
