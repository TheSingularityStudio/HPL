"""
HPL 智能错误建议引擎

该模块提供智能错误分析和建议功能，帮助开发者快速定位和修复问题。

关键类：
- ErrorSuggestionEngine: 智能错误建议引擎

主要功能：
- 拼写错误检测和纠正建议
- 相似变量名查找
- 类型错误模式识别
- 快速修复代码生成
"""

import difflib
import re
from typing import List, Dict, Optional, Any, Callable


class ErrorSuggestionEngine:
    """
    智能错误建议引擎
    
    分析错误上下文，提供智能修复建议。
    """
    
    # 常见拼写错误映射
    COMMON_MISSPELLINGS = {
        # 内置函数
        'pritn': 'print',
        'prnit': 'print',
        'ptint': 'print',
        'fucntion': 'function',
        'funtion': 'function',
        'funciton': 'function',
        'calss': 'class',
        'clss': 'class',
        'clsas': 'class',
        'retunr': 'return',
        'retrun': 'return',
        'retun': 'return',
        'ture': 'true',
        'treu': 'true',
        'flase': 'false',
        'fasle': 'false',
        'nulll': 'null',
        'nul': 'null',
        'nuull': 'null',
        'lengh': 'length',
        'lenght': 'length',
        'appen': 'append',
        'appned': 'append',
        'remvoe': 'remove',
        'remoev': 'remove',
        'inlcude': 'include',
        'incldue': 'include',
        'improt': 'import',
        'imoprt': 'import',
        'elss': 'else',
        'eles': 'else',
        'whlie': 'while',
        'whiel': 'while',
        'fro': 'for',
        'braek': 'break',
        'breka': 'break',
        'contniue': 'continue',
        'contineu': 'continue',
        'catsh': 'catch',
        'ctach': 'catch',
        'finnaly': 'finally',
        'finalyl': 'finally',
        'thrw': 'throw',
        'thow': 'throw',
        'tyr': 'try',
        'tyr': 'try',
        'swicth': 'switch',
        'swtich': 'switch',
        'casee': 'case',
        'caes': 'case',
        'defualt': 'default',
        'defautl': 'default',
    }
    
    # 类型错误模式和建议
    TYPE_ERROR_PATTERNS = {
        'int_str_addition': {
            'pattern': r'Cannot add.*int.*str|Cannot add.*str.*int',
            'suggestion': '使用 str() 将数字转换为字符串: str({left}) + {right}',
            'example': 'str(42) + " items"',
        },
        'list_index_str': {
            'pattern': r'Array index must be integer, got str',
            'suggestion': '使用 int() 将字符串转换为整数索引: int({index})',
            'example': 'arr[int("0")]',
        },
        'none_operation': {
            'pattern': r'Cannot.*NoneType',
            'suggestion': '检查变量是否为 null，在使用前进行初始化或赋值',
            'example': 'if (x != null) : result = x + 1',
        },
        'str_arithmetic': {
            'pattern': r'Arithmetic.*str',
            'suggestion': '字符串不能直接进行算术运算，使用 int() 或 float() 转换: int({value})',
            'example': 'int("42") + 1',
        },
    }
    
    def __init__(self, global_scope: Optional[Dict] = None, 
                 local_scope: Optional[Dict] = None,
                 evaluator=None):
        """
        初始化建议引擎
        
        Args:
            global_scope: 全局变量作用域
            local_scope: 局部变量作用域
            evaluator: HPLEvaluator 实例（用于获取额外上下文）
        """
        self.global_scope = global_scope or {}
        self.local_scope = local_scope or {}
        self.evaluator = evaluator
    
    def set_scopes(self, global_scope: Dict, local_scope: Dict):
        """更新作用域信息"""
        self.global_scope = global_scope
        self.local_scope = local_scope
    
    def suggest_for_name_error(self, name: str) -> List[str]:
        """
        为未定义变量提供建议
        
        Args:
            name: 未定义的变量名
        
        Returns:
            建议列表
        """
        suggestions = []
        
        # 1. 检查常见拼写错误
        if name in self.COMMON_MISSPELLINGS:
            correct = self.COMMON_MISSPELLINGS[name]
            suggestions.append(f"您是不是想输入 '{correct}'?")
        
        # 2. 查找相似名称
        all_names = self._get_all_available_names()
        similar = self._find_similar_names(name, all_names, threshold=0.6, max_results=3)
        if similar:
            if len(similar) == 1:
                suggestions.append(f"您是不是想使用变量 '{similar[0]}'?")
            else:
                suggestions.append(f"您是不是想使用: {', '.join(similar)}?")
        
        # 3. 检查作用域问题
        if name in self.global_scope and name not in self.local_scope:
            suggestions.append(f"'{name}' 在全局作用域中定义，但可能在此上下文中不可访问")
        
        # 4. 检查是否是内置函数
        builtin_names = ['print', 'len', 'int', 'str', 'float', 'bool', 'type', 
                        'abs', 'max', 'min', 'range', 'input', 'echo']
        if name in builtin_names:
            suggestions.append(f"'{name}' 是内置函数，可以直接使用")
        
        return suggestions
    
    def suggest_for_type_error(self, operation: str, left_type: str, 
                              right_type: str, message: str = "") -> List[str]:
        """
        为类型错误提供建议
        
        Args:
            operation: 操作符或操作名称
            left_type: 左操作数类型
            right_type: 右操作数类型
            message: 原始错误消息
        
        Returns:
            建议列表
        """
        suggestions = []
        
        # 检查已知模式
        for pattern_name, pattern_info in self.TYPE_ERROR_PATTERNS.items():
            if re.search(pattern_info['pattern'], message, re.IGNORECASE):
                suggestion = pattern_info['suggestion']
                example = pattern_info['example']
                suggestions.append(f"{suggestion}\n   示例: {example}")
                break
        
        # 常见类型错误模式
        if operation == '+' and ('str' in [left_type, right_type]):
            if 'int' in [left_type, right_type] or 'float' in [left_type, right_type]:
                suggestions.append(
                    f"要将 {left_type} 和 {right_type} 连接，"
                    f"需要将数字转换为字符串: str(value)"
                )
        
        if operation in ('-', '*', '/', '%') and 'str' in [left_type, right_type]:
            suggestions.append(
                f"算术运算需要数字类型。使用 int() 或 float() 转换字符串: "
                f"int({left_type if left_type == 'str' else right_type}_value)"
            )
        
        if 'NoneType' in [left_type, right_type]:
            suggestions.append(
                "变量可能未初始化。在使用前检查是否为 null: "
                "if (var != null) : result = var + 1"
            )
        
        # 数组操作错误
        if operation == '[]' and left_type != 'list':
            suggestions.append(
                f"只有数组和字符串可以使用索引访问。{left_type} 类型不支持索引操作。"
            )
            if left_type == 'dict':
                suggestions.append("字典使用键访问: dict[key] 或 dict.get(key)")
        
        return suggestions
    
    def suggest_for_index_error(self, index: int, length: int, 
                               array_type: str = "array") -> List[str]:
        """
        为索引错误提供建议
        
        Args:
            index: 越界的索引值
            length: 数组长度
            array_type: 数组类型描述
        
        Returns:
            建议列表
        """
        suggestions = []
        
        if length == 0:
            suggestions.append(f"{array_type} 为空，无法访问任何索引")
            return suggestions
        
        # 负索引建议
        if index < 0:
            reverse_index = length + index
            if 0 <= reverse_index < length:
                suggestions.append(
                    f"使用反向索引 {reverse_index} 可以访问倒数第 {abs(index)} 个元素"
                )
            else:
                suggestions.append(f"索引 {index} 太小，最小有效索引为 {-length}")
        
        # 超出范围建议
        if index >= length:
            suggestions.append(f"最大有效索引是 {length - 1}（数组长度为 {length}）")
            suggestions.append(f"有效索引范围: 0 到 {length - 1}")
        
        # 动态计算建议
        if index > length:
            suggestions.append(f"考虑使用动态索引计算: index % {length}")
        
        return suggestions
    
    def suggest_for_key_error(self, key: Any, available_keys: List[Any]) -> List[str]:
        """
        为字典键错误提供建议
        
        Args:
            key: 不存在的键
            available_keys: 可用的键列表
        
        Returns:
            建议列表
        """
        suggestions = []
        
        # 查找相似的键
        key_strs = [str(k) for k in available_keys]
        similar = difflib.get_close_matches(str(key), key_strs, n=2, cutoff=0.6)
        if similar:
            if len(similar) == 1:
                suggestions.append(f"您是不是想使用键 '{similar[0]}'?")
            else:
                suggestions.append(f"相似的键: {', '.join(similar)}")
        
        # 键类型建议
        if isinstance(key, int) and any(isinstance(k, str) and str(key) == k for k in available_keys):
            suggestions.append(f"尝试使用字符串键: \"{key}\"")
        elif isinstance(key, str) and key.isdigit() and any(isinstance(k, int) and str(k) == key for k in available_keys):
            suggestions.append(f"尝试使用整数键: {int(key)}")
        
        # 检查键是否存在
        suggestions.append(f"在使用前检查键是否存在: if (\"{key}\" in dict) : value = dict[\"{key}\"]")
        
        return suggestions
    
    def suggest_for_import_error(self, module_name: str, error_message: str = "") -> List[str]:
        """
        为导入错误提供建议
        
        Args:
            module_name: 模块名称
            error_message: 原始错误消息
        
        Returns:
            建议列表
        """
        suggestions = []
        
        # 检查是否是标准库模块
        stdlib_modules = ['io', 'math', 'time', 'os', 'json']
        if module_name.lower() in stdlib_modules:
            suggestions.append(f"'{module_name}' 是 HPL 标准库模块，确保拼写正确")
        
        # 检查拼写
        available_modules = stdlib_modules + self._get_available_modules()
        similar = difflib.get_close_matches(module_name, available_modules, n=2, cutoff=0.6)
        if similar:
            suggestions.append(f"您是不是想导入: {', '.join(similar)}?")
        
        # Python 模块建议
        if "No module named" in error_message:
            suggestions.append(f"Python 模块未找到。尝试安装: pip install {module_name}")
        
        # 文件路径建议
        if '.' in module_name:
            suggestions.append("确保模块文件路径正确，并使用正确的相对路径")
        
        return suggestions
    
    def suggest_for_division_error(self) -> List[str]:
        """
        为除零错误提供建议
        
        Returns:
            建议列表
        """
        return [
            "添加除零检查: if (divisor != 0) : result = dividend / divisor",
            "使用条件表达式: result = (divisor != 0) ? (dividend / divisor) : 0",
            "确保除数在使用前已正确初始化且不为零",
        ]
    
    def suggest_for_attribute_error(self, obj_type: str, attr_name: str,
                                   available_attrs: List[str]) -> List[str]:
        """
        为属性错误提供建议
        
        Args:
            obj_type: 对象类型
            attr_name: 不存在的属性名
            available_attrs: 可用属性列表
        
        Returns:
            建议列表
        """
        suggestions = []
        
        # 查找相似属性
        similar = difflib.get_close_matches(attr_name, available_attrs, n=2, cutoff=0.6)
        if similar:
            if len(similar) == 1:
                suggestions.append(f"您是不是想访问 '{similar[0]}'?")
            else:
                suggestions.append(f"相似的属性: {', '.join(similar)}")
        
        # 类型特定建议
        if obj_type == 'dict':
            suggestions.append(f"字典的键: {available_keys[:5] if (available_keys := list(available_attrs)) else '空字典'}")
        elif obj_type == 'HPLObject':
            suggestions.append("确保对象已正确初始化，类定义中包含该属性或方法")
        
        return suggestions
    
    def get_quick_fix(self, error_type: str, error_message: str, 
                     context: Optional[Dict] = None) -> Optional[str]:
        """
        获取快速修复代码
        
        Args:
            error_type: 错误类型类名
            error_message: 错误消息
            context: 错误上下文信息
        
        Returns:
            快速修复代码字符串，如果没有则返回 None
        """
        quick_fixes = {
            'HPLNameError': self._fix_name_error,
            'HPLTypeError': self._fix_type_error,
            'HPLIndexError': self._fix_index_error,
            'HPLDivisionError': self._fix_division_error,
        }
        
        fixer = quick_fixes.get(error_type)
        if fixer:
            return fixer(error_message, context)
        return None
    
    def _fix_name_error(self, message: str, context: Optional[Dict]) -> Optional[str]:
        """生成变量名错误的修复建议"""
        # 从错误消息中提取变量名
        match = re.search(r"'(\w+)'|Undefined variable:\s*'(\w+)'", message)
        if match:
            var_name = match.group(1) or match.group(2)
            return f"# 添加变量定义\\n{var_name} = null  # 或适当的初始值"
        return None
    
    def _fix_type_error(self, message: str, context: Optional[Dict]) -> Optional[str]:
        """生成类型错误的修复建议"""
        if "Cannot add" in message and "int" in message and "str" in message:
            return "# 使用类型转换\\nresult = str(left_value) + str(right_value)"
        elif "Array index must be integer" in message:
            return "# 转换索引为整数\\nindex = int(index_str)\\nvalue = arr[index]"
        elif "Cannot index" in message:
            return "# 检查类型后再访问\\nif (type(arr) == 'array') : value = arr[index]"
        return None
    
    def _fix_index_error(self, message: str, context: Optional[Dict]) -> Optional[str]:
        """生成索引错误的修复建议"""
        # 提取索引和长度信息
        match = re.search(r'index\s+(-?\d+)\s+out of bounds.*length\s+(\d+)', message)
        if match:
            index = int(match.group(1))
            length = int(match.group(2))
            
            if index < 0:
                return f"# 使用正向索引\\n# 原索引 {index} 转换为 {length + index}"
            else:
                return f"# 检查索引边界\\nif (index >= 0 && index < {length}) : value = arr[index]"
        return "# 检查数组长度后再访问\\nif (index < len(arr)) : value = arr[index]"
    
    def _fix_division_error(self, message: str, context: Optional[Dict]) -> Optional[str]:
        """生成除零错误的修复建议"""
        return "# 添加除零保护\\nif (divisor != 0) :\\n    result = dividend / divisor\\nelse :\\n    result = 0  # 或适当的默认值"
    
    def _find_similar_names(self, target: str, candidates: List[str], 
                           threshold: float = 0.6, max_results: int = 3) -> List[str]:
        """
        查找相似的名称
        
        Args:
            target: 目标名称
            candidates: 候选名称列表
            threshold: 相似度阈值
            max_results: 最大返回结果数
        
        Returns:
            相似的名称列表
        """
        if not candidates:
            return []
        
        matches = difflib.get_close_matches(target, candidates, n=max_results, cutoff=threshold)
        return matches
    
    def _get_all_available_names(self) -> List[str]:
        """获取所有可用的变量名"""
        names = set()
        names.update(self.local_scope.keys())
        names.update(self.global_scope.keys())
        return list(names)
    
    def _get_available_modules(self) -> List[str]:
        """获取可用的模块列表"""
        # 这里可以扩展为动态获取可用模块
        return []
    
    def analyze_error(self, error, local_scope: Optional[Dict] = None) -> Dict[str, Any]:
        """
        全面分析错误并返回所有相关建议

        Args:
            error: 错误对象
            local_scope: 当前局部作用域

        Returns:
            包含所有建议的字典
        """
        if local_scope:
            self.local_scope = local_scope

        result = {
            'error_type': error.__class__.__name__,
            'message': str(error),
            'suggestions': [],
            'quick_fix': None,
            'context_info': {},
        }

        error_type = error.__class__.__name__
        message = str(error)

        # 提取上下文信息
        result['context_info'] = self._extract_context_info(error, message)

        # 根据错误类型获取建议
        if error_type == 'HPLNameError':
            # 提取变量名
            match = re.search(r"'(\w+)'|Undefined variable:\s*'(\w+)'", message)
            if match:
                var_name = match.group(1) or match.group(2)
                result['suggestions'] = self.suggest_for_name_error(var_name)

        elif error_type == 'HPLTypeError':
            # 更智能的类型错误分析
            operation, left_type, right_type = self._analyze_type_error(message)
            result['suggestions'] = self.suggest_for_type_error(
                operation, left_type, right_type, message
            )

        elif error_type == 'HPLIndexError':
            # 尝试提取索引和长度
            match = re.search(r'index\s+(-?\d+)\s+out of bounds.*length\s+(\d+)', message)
            if match:
                index = int(match.group(1))
                length = int(match.group(2))
                result['suggestions'] = self.suggest_for_index_error(index, length)

        elif error_type == 'HPLKeyError':
            # 字典键错误
            match = re.search(r"Key\s+([^']+)\s+\(type:\s+(\w+)\)\s+not found", message)
            if match:
                key = match.group(1)
                key_type = match.group(2)
                available_keys = self._extract_available_keys(message)
                result['suggestions'] = self.suggest_for_key_error(key, available_keys)

        elif error_type == 'HPLDivisionError':
            result['suggestions'] = self.suggest_for_division_error()

        elif error_type == 'HPLImportError':
            # 提取模块名
            match = re.search(r"module\s+'(\w+)'|Cannot import module\s+'(\w+)'", message)
            if match:
                module_name = match.group(1) or match.group(2)
                result['suggestions'] = self.suggest_for_import_error(module_name, message)

        elif error_type == 'HPLAttributeError':
            # 属性错误
            match = re.search(r"Method or attribute\s+'(\w+)'\s+not found", message)
            if match:
                attr_name = match.group(1)
                available_attrs = self._get_available_attributes(error)
                result['suggestions'] = self.suggest_for_attribute_error(
                    'object', attr_name, available_attrs
                )

        # 获取快速修复
        result['quick_fix'] = self.get_quick_fix(error_type, message)

        return result

    def _extract_context_info(self, error, message: str) -> Dict[str, Any]:
        """从错误消息中提取上下文信息"""
        context = {}

        # 提取行号和列号
        if hasattr(error, 'line') and error.line:
            context['line'] = error.line
        if hasattr(error, 'column') and error.column:
            context['column'] = error.column

        # 提取文件名
        if hasattr(error, 'file') and error.file:
            context['file'] = error.file

        # 提取操作类型
        if 'Cannot index' in message:
            context['operation'] = 'indexing'
        elif 'Cannot convert' in message:
            context['operation'] = 'conversion'
        elif 'Undefined variable' in message:
            context['operation'] = 'variable_lookup'
        elif 'not found in dictionary' in message:
            context['operation'] = 'dict_access'

        return context

    def _analyze_type_error(self, message: str) -> tuple:
        """分析类型错误，提取操作和类型信息"""
        operation = 'unknown'
        left_type = 'unknown'
        right_type = 'unknown'

        # 分析常见的类型错误模式
        if 'Cannot add' in message or 'Cannot concatenate' in message:
            operation = '+'
            # 尝试提取类型
            match = re.search(r'int.*str|str.*int|float.*str|str.*float', message)
            if match:
                types = match.group(0).split()
                left_type, right_type = types[0], types[2]

        elif 'Array index must be integer' in message:
            operation = 'indexing'
            match = re.search(r'got\s+(\w+)', message)
            if match:
                right_type = match.group(1)

        elif 'Logical NOT requires boolean' in message:
            operation = 'logical_not'
            match = re.search(r'got\s+(\w+)', message)
            if match:
                right_type = match.group(1)

        elif 'requires number' in message:
            operation = 'arithmetic'
            match = re.search(r'got\s+(\w+)', message)
            if match:
                right_type = match.group(1)

        return operation, left_type, right_type

    def _extract_available_keys(self, message: str) -> List[Any]:
        """从错误消息中提取可用的键"""
        match = re.search(r'Available keys:\s*\[([^\]]+)\]', message)
        if match:
            keys_str = match.group(1)
            # 简单解析，实际可能需要更复杂的解析
            try:
                return eval(f'[{keys_str}]')
            except:
                return []
        return []

    def _get_available_attributes(self, error) -> List[str]:
        """获取对象可用的属性（需要从错误上下文中获取）"""
        # 这里可以扩展为从错误对象中获取更多上下文
        # 目前返回空列表，实际实现需要更多上下文信息
        return []


# 便捷函数
def create_suggestion_engine(global_scope=None, local_scope=None, evaluator=None):
    """
    创建建议引擎的工厂函数
    
    Args:
        global_scope: 全局作用域
        local_scope: 局部作用域
        evaluator: HPLEvaluator 实例
    
    Returns:
        ErrorSuggestionEngine 实例
    """
    return ErrorSuggestionEngine(global_scope, local_scope, evaluator)


def get_smart_suggestions(error, global_scope=None, local_scope=None) -> List[str]:
    """
    获取错误的智能建议（便捷函数）
    
    Args:
        error: 错误对象
        global_scope: 全局作用域
        local_scope: 局部作用域
    
    Returns:
        建议列表
    """
    engine = ErrorSuggestionEngine(global_scope, local_scope)
    analysis = engine.analyze_error(error, local_scope)
    return analysis['suggestions']
