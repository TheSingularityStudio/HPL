# HPL Runtime 错误处理系统分析报告（修正版）

## 执行摘要

经过对 HPL 运行时错误处理系统的全面分析，发现当前系统具有良好的基础架构，但在错误恢复、上下文丰富度、开发者体验等方面存在改进空间。本报告提供详细的改进建议和实现方案。

---

## 1. 当前架构评估

### 1.1 优势

| 特性 | 实现状态 | 评价 |
|------|---------|------|
| 异常层次结构 | ✅ 完整 | HPLError → 具体错误类型，设计良好 |
| 位置信息跟踪 | ✅ 支持 | 行号、列号、文件名 |
| 调用栈跟踪 | ✅ 支持 | 运行时错误包含调用链 |
| 源代码上下文 | ✅ 支持 | 可视化代码片段和错误指示器 |
| 控制流分离 | ✅ 支持 | break/continue/return 作为独立异常 |
| 调试工具 | ✅ 支持 | ErrorAnalyzer 提供详细诊断 |

### 1.2 核心组件关系图

```
┌─────────────────────────────────────────────────────────────┐
│                      错误处理架构                             │
├─────────────────────────────────────────────────────────────┤
│  HPLError (基类)                                             │
│  ├── HPLSyntaxError      ← 词法/语法错误                     │
│  ├── HPLRuntimeError     ← 运行时错误（含调用栈）             │
│  │   ├── HPLTypeError                                      │
│  │   ├── HPLNameError                                       │
│  │   ├── HPLAttributeError                                  │
│  │   ├── HPLIndexError                                      │
│  │   ├── HPLDivisionError                                    │
│  │   ├── HPLValueError                                       │
│  │   ├── HPLIOError                                          │
│  │   └── HPLRecursionError                                    │
│  ├── HPLImportError        ← 导入错误                        │
│  └── HPLControlFlowException ← 控制流（非错误）               │
│      ├── HPLBreakException                                   │
│      ├── HPLContinueException                                │
│      └── HPLReturnValue                                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  错误处理层                                                   │
│  ├── format_error_for_user()    ← 用户友好格式化             │
│  ├── ErrorAnalyzer              ← 详细分析                   │
│  │   ├── ErrorTracer            ← 错误跟踪                   │
│  │   ├── CallStackAnalyzer      ← 调用栈分析                 │
│  │   ├── VariableInspector      ← 变量检查                   │
│  │   └── ExecutionLogger        ← 执行日志                   │
│  └── DebugInterpreter           ← 调试模式解释器             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 需要改进的领域

### 2.1 错误恢复机制（优先级：高）

#### 当前问题
```python
# evaluator.py - 当前 try-catch 实现
elif isinstance(stmt, TryCatchStatement):
    try:
        result = self.execute_block(stmt.try_block, local_scope)
    except HPLRuntimeError as e:
        local_scope[stmt.catch_var] = str(e)  # 只捕获字符串消息
        result = self.execute_block(stmt.catch_block, local_scope)
    except HPLBreakException:
        raise  # 控制流异常需要继续传播
    except HPLContinueException:
        raise
```

**问题：**
1. 缺少 `finally` 块支持
2. 错误对象信息丢失（只传递字符串）
3. 无法重新抛出原始错误
4. 没有错误类型过滤

#### 建议改进

```python
# 改进后的 TryCatchStatement 模型
class TryCatchStatement(Statement):
    def __init__(self, try_block, catch_clauses, finally_block=None):
        self.try_block = try_block
        self.catch_clauses = catch_clauses  # 支持多 catch
        self.finally_block = finally_block  # 可选 finally
    
class CatchClause:
    def __init__(self, error_type, var_name, block):
        self.error_type = error_type  # 特定错误类型或 None（捕获所有）
        self.var_name = var_name
        self.block = block
```

```python
# 改进后的执行逻辑
elif isinstance(stmt, TryCatchStatement):
    caught = False
    error_obj = None
    
    try:
        result = self.execute_block(stmt.try_block, local_scope)
        if isinstance(result, HPLReturnValue):
            return result
    except HPLRuntimeError as e:
        error_obj = e
        
        # 尝试匹配特定的 catch 子句
        for catch in stmt.catch_clauses:
            if catch.error_type is None or self._matches_error_type(e, catch.error_type):
                local_scope[catch.var_name] = e  # 传递完整错误对象
                result = self.execute_block(catch.block, local_scope)
                caught = True
                if isinstance(result, HPLReturnValue):
                    return result
                break
        
        if not caught:
            raise  # 重新抛出未捕获的错误
    finally:
        # 执行 finally 块（如果有）
        if stmt.finally_block:
            finally_result = self.execute_block(stmt.finally_block, local_scope)
            # finally 中的 return 会覆盖 try/catch 中的 return
            if isinstance(finally_result, HPLReturnValue):
                return finally_result
```

#### 语法支持（修正为正确的 HPL 语法）

```yaml
# 当前语法
try :
  risky_operation()
catch (err) :
  handle_error(err)

# 改进后语法 - 支持多 catch 和 finally
try :
  risky_operation()
catch HPLTypeError (type_err) :
  handle_type_error(type_err)
catch HPLNameError (name_err) :
  handle_name_error(name_err)
catch (err) :  # 捕获所有其他错误
  handle_generic_error(err)
finally :
  cleanup_resources()  # 总是执行
```

---

### 2.2 错误上下文丰富度（优先级：高）

#### 当前问题
错误发生时缺少运行时上下文信息，调试困难。

#### 建议改进：增强错误上下文

```python
# 在 exceptions.py 中添加
class HPLRuntimeError(HPLError):
    def __init__(self, message, line=None, column=None, file=None, context=None,
                 call_stack=None, error_code=None, **kwargs):
        super().__init__(message, line, column, file, context, error_code)
        self.call_stack = call_stack or []
        # 新增上下文信息
        self.variable_snapshot = kwargs.get('variable_snapshot', {})
        self.execution_trace = kwargs.get('execution_trace', [])
        self.function_args = kwargs.get('function_args', {})
        self.recent_assignments = kwargs.get('recent_assignments', [])
    
    def enrich_context(self, evaluator, local_scope):
        """从 evaluator 捕获运行时上下文"""
        if evaluator:
            # 捕获变量状态
            self.variable_snapshot = {
                'local': {k: v for k, v in local_scope.items() if not k.startswith('_')},
                'global_keys': list(evaluator.global_scope.keys()),
                'current_obj': evaluator.current_obj
            }
            # 捕获最近执行轨迹
            if hasattr(evaluator, 'exec_logger'):
                self.execution_trace = evaluator.exec_logger.get_trace(last_n=10)
```

```python
# 在 evaluator.py 中统一错误增强
def _create_error(self, error_class, message, line=None, column=None, 
                local_scope=None, **kwargs):
    """统一创建错误并添加上下文"""
    error = error_class(
        message=message,
        line=line,
        column=column,
        file=getattr(self, 'current_file', None),
        call_stack=self.call_stack.copy(),
        **kwargs
    )
    
    # 自动丰富上下文
    if local_scope is not None:
        error.enrich_context(self, local_scope)
    
    return error

# 使用示例
raise self._create_error(
    HPLTypeError,
    f"Cannot index non-array value: {type(array).__name__}",
    stmt.line, 
    stmt.column,
    local_scope
)
```

---

### 2.3 错误代码系统完善（优先级：中）

#### 当前问题
- 错误代码存在但未充分利用
- 缺少错误代码文档
- 用户无法通过错误代码快速查找解决方案

#### 建议改进

```python
# exceptions.py - 增强错误代码系统
class HPLError(Exception):
    # 错误代码前缀
    ERROR_CODE_PREFIX = "HPL"
    
    # 错误代码映射表
    ERROR_CODE_MAP = {
        # 语法错误 (1xx)
        'SYNTAX_UNEXPECTED_TOKEN': 'HPL-SYNTAX-101',
        'SYNTAX_MISSING_BRACKET': 'HPL-SYNTAX-102',
        'SYNTAX_INVALID_INDENT': 'HPL-SYNTAX-103',
        'SYNTAX_YAML_ERROR': 'HPL-SYNTAX-150',
        
        # 运行时错误 (2xx)
        'RUNTIME_UNDEFINED_VAR': 'HPL-RUNTIME-201',
        'RUNTIME_TYPE_MISMATCH': 'HPL-RUNTIME-202',
        'RUNTIME_INDEX_OUT_OF_BOUNDS': 'HPL-RUNTIME-203',
        'RUNTIME_DIVISION_BY_ZERO': 'HPL-RUNTIME-204',
        'RUNTIME_NULL_POINTER': 'HPL-RUNTIME-205',
        'RUNTIME_RECURSION_DEPTH': 'HPL-RUNTIME-206',
        
        # 类型错误 (3xx)
        'TYPE_INVALID_OPERATION': 'HPL-TYPE-301',
        'TYPE_CONVERSION_FAILED': 'HPL-TYPE-302',
        'TYPE_MISSING_PROPERTY': 'HPL-TYPE-303',
        
        # 导入错误 (4xx)
        'IMPORT_MODULE_NOT_FOUND': 'HPL-IMPORT-401',
        'IMPORT_CIRCULAR': 'HPL-IMPORT-402',
        'IMPORT_VERSION_MISMATCH': 'HPL-IMPORT-403',
        
        # IO 错误 (5xx)
        'IO_FILE_NOT_FOUND': 'HPL-IO-501',
        'IO_PERMISSION_DENIED': 'HPL-IO-502',
        'IO_READ_ERROR': 'HPL-IO-503',
    }
    
    def __init__(self, message, line=None, column=None, file=None, 
                 context=None, error_code=None, error_key=None):
        # 支持通过 error_key 自动获取错误代码
        if error_key and not error_code:
            error_code = self.ERROR_CODE_MAP.get(error_key)
        
        self.error_code = error_code
        # ... 其余初始化代码
    
    def get_help_url(self):
        """获取帮助文档链接"""
        if self.error_code:
            base_url = "https://hpl-lang.org/docs/errors"
            return f"{base_url}/{self.error_code.lower()}"
        return None
```

```python
# 改进错误格式化，包含帮助信息
def format_error_for_user(error, source_code=None):
    # ... 现有代码 ...
    
    # 添加帮助链接
    help_url = error.get_help_url()
    if help_url:
        lines.append(f"\n   📖 帮助文档: {help_url}")
    
    # 添加错误解决建议
    suggestion = get_error_suggestion(error)
    if suggestion:
        lines.append(f"\n   💡 建议: {suggestion}")
    
    return '\n'.join(lines)

def get_error_suggestion(error):
    """根据错误类型提供解决建议"""
    suggestions = {
        'HPLNameError': "检查变量名拼写，或确认变量已在使用前定义",
        'HPLTypeError': "检查操作数的类型，必要时使用类型转换函数 int() 或 str()",
        'HPLIndexError': "检查数组长度和索引值，确保 0 <= index < len(array)",
        'HPLDivisionError': "添加除零检查，如: if (divisor != 0) : result = dividend / divisor",
        'HPLImportError': "检查模块名称拼写，或确认模块已正确安装",
    }
    return suggestions.get(error.__class__.__name__)
```

---

### 2.4 错误报告一致性（优先级：中）

#### 当前问题
- `interpreter.py` 和 `debug_interpreter.py` 错误处理逻辑重复
- 错误格式化逻辑分散
- 缺少统一的错误处理中间件

#### 建议改进：统一错误处理

```python
# 新增 error_handler.py 模块
class HPLErrorHandler:
    """统一的错误处理中间件"""
    
    def __init__(self, source_code=None, debug_mode=False):
        self.source_code = source_code
        self.debug_mode = debug_mode
        self.analyzer = ErrorAnalyzer() if debug_mode else None
    
    def handle(self, error, evaluator=None, exit_on_error=True):
        """
        统一处理错误
        
        Args:
            error: 异常对象
            evaluator: 可选的 evaluator 实例（用于获取上下文）
            exit_on_error: 是否退出程序
        
        Returns:
            格式化的错误字符串（如果不退出）
        """
        # 增强错误信息
        if evaluator and isinstance(error, HPLRuntimeError):
            if not error.call_stack:
                error.call_stack = evaluator.call_stack.copy()
        
        # 生成错误报告
        if self.debug_mode and self.analyzer:
            context = self.analyzer.analyze_error(
                error, 
                source_code=self.source_code,
                evaluator=evaluator
            )
            report = self.analyzer.generate_report(context)
        else:
            report = format_error_for_user(error, self.source_code)
        
        if exit_on_error:
            print(report)
            sys.exit(1)
        else:
            return report
    
    def handle_syntax_error(self, error, parser=None):
        """专门处理语法错误"""
        source = getattr(parser, 'source_code', self.source_code)
        print(format_error_for_user(error, source))
        sys.exit(1)
    
    def handle_unexpected_error(self, error, hpl_file):
        """处理未预期的内部错误"""
        import traceback
        
        # 包装为 HPLRuntimeError
        wrapped = HPLRuntimeError(
            f"Internal error: {type(error).__name__}: {str(error)}",
            file=hpl_file,
            error_key='RUNTIME_INTERNAL'
        )
        
        print(format_error_for_user(wrapped))
        
        if self.debug_mode or os.environ.get('HPL_DEBUG'):
            print("\n--- Full traceback ---")
            traceback.print_exc()
        
        sys.exit(1)
```

```python
# 简化后的 interpreter.py
def main():
    # ... 参数检查 ...
    
    set_current_hpl_file(hpl_file)
    handler = None
    
    try:
        with open(hpl_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        handler = HPLErrorHandler(source_code, debug_mode=False)
        
        parser = HPLParser(hpl_file)
        # ... 解析和执行代码 ...
        
    except HPLSyntaxError as e:
        handler.handle_syntax_error(e, parser if 'parser' in locals() else None)
    except HPLRuntimeError as e:
        handler.handle(e, evaluator if 'evaluator' in locals() else None)
    except HPLImportError as e:
        handler.handle(e)
    except HPLError as e:
        handler.handle(e)
    except FileNotFoundError as e:
        print(f"[ERROR] File not found: {e.filename}")
        sys.exit(1)
    except Exception as e:
        handler.handle_unexpected_error(e, hpl_file)
```

---

### 2.5 边缘情况处理增强（优先级：中）

#### 当前问题
- 数组/字典访问错误信息不够具体
- 类型转换错误缺少上下文
- 数学运算错误覆盖不全

#### 建议改进

```python
# 增强数组访问错误
def _handle_array_access(self, array, index, expr, local_scope):
    """统一的数组/字典访问处理"""
    
    # 类型检查
    if not isinstance(array, (list, dict, str)):
        # 提供更具体的错误信息
        actual_type = type(array).__name__
        hint = ""
        if actual_type == 'int':
            hint = " (did you mean to access a digit? numbers are not indexable)"
        elif actual_type == 'NoneType':
            hint = " (variable may not be initialized)"
        
        raise HPLTypeError(
            f"Cannot index {actual_type} value{hint}",
            line=expr.line,
            column=expr.column,
            error_key='TYPE_INVALID_OPERATION'
        )
    
    # 索引类型检查
    if isinstance(array, (list, str)) and not isinstance(index, int):
        raise HPLTypeError(
            f"Array index must be integer, got {type(index).__name__} (value: {index!r})",
            line=expr.line,
            column=expr.column,
            error_key='TYPE_INVALID_OPERATION'
        )
    
    # 边界检查（提供更详细的边界信息）
    if isinstance(array, (list, str)):
        length = len(array)
        if index < 0 or index >= length:
            # 提供有用的边界信息
            suggestions = []
            if index < 0:
                suggestions.append(f"use {length + index} for reverse indexing")
            if length > 0:
                suggestions.append(f"valid range: 0 to {length-1}")
            
            hint = f". " + " or ".join(suggestions) if suggestions else ""
            
            raise HPLIndexError(
                f"Index {index} out of bounds for {actual_type} of length {length}{hint}",
                line=expr.line,
                column=expr.column,
                error_key='RUNTIME_INDEX_OUT_OF_BOUNDS'
            )
    
    # 字典键检查
    if isinstance(array, dict) and index not in array:
        available_keys = list(array.keys())[:5]  # 显示前5个可用键
        hint = f" Available keys: {available_keys}" if available_keys else " Dictionary is empty."
        
        raise HPLKeyError(  # 新增错误类型
            f"Key {index!r} not found in dictionary.{hint}",
            line=expr.line,
            column=expr.column,
            error_key='RUNTIME_KEY_NOT_FOUND'
        )
    
    return array[index]
```

```python
# 新增 HPLKeyError 到 exceptions.py
class HPLKeyError(HPLRuntimeError):
    """字典键不存在错误"""
    pass
```

```python
# 增强类型转换错误
def _handle_type_conversion(self, value, target_type, expr):
    """统一的类型转换处理"""
    converters = {
        'int': (int, (ValueError, TypeError)),
        'float': (float, (ValueError, TypeError)),
        'str': (str, ()),
        'bool': (bool, ()),
        'list': (list, (TypeError,)),
    }
    
    if target_type not in converters:
        raise HPLValueError(f"Unknown type conversion target: {target_type}")
    
    converter, expected_errors = converters[target_type]
    
    try:
        return converter(value)
    except expected_errors as e:
        raise HPLTypeError(
            f"Cannot convert {type(value).__name__} (value: {value!r}) to {target_type}: {str(e)}",
            line=expr.line,
            column=expr.column,
            error_key='TYPE_CONVERSION_FAILED'
        )
```

---

### 2.6 开发者体验改进（优先级：高）

#### 建议改进：智能错误提示

```python
# 新增 error_suggestions.py 模块
class ErrorSuggestionEngine:
    """智能错误建议引擎"""
    
    COMMON_MISSPELLINGS = {
        'pritn': 'print',
        'fucntion': 'function',
        'calss': 'class',
        'retunr': 'return',
        'ture': 'true',
        'flase': 'false',
        'nulll': 'null',
    }
    
    def __init__(self, global_scope, local_scope):
        self.global_scope = global_scope
        self.local_scope = local_scope
    
    def suggest_for_name_error(self, name):
        """为未定义变量提供建议"""
        suggestions = []
        
        # 1. 检查拼写错误
        if name in self.COMMON_MISSPELLINGS:
            correct = self.COMMON_MISSPELLINGS[name]
            suggestions.append(f"Did you mean '{correct}'?")
        
        # 2. 查找相似名称（使用 Levenshtein 距离）
        all_names = set(self.global_scope.keys()) | set(self.local_scope.keys())
        similar = self._find_similar_names(name, all_names, threshold=2)
        if similar:
            suggestions.append(f"Did you mean: {', '.join(similar)}?")
        
        # 3. 检查作用域问题
        if name in self.global_scope and name not in self.local_scope:
            suggestions.append(f"'{name}' is defined in global scope but not accessible here")
        
        return suggestions
    
    def suggest_for_type_error(self, operation, left_type, right_type):
        """为类型错误提供建议"""
        suggestions = []
        
        # 常见类型错误模式
        if operation == '+' and (left_type == 'str' or right_type == 'str'):
            suggestions.append(
                f"To concatenate {left_type} and {right_type}, "
                f"convert both to strings: str(left) + str(right)"
            )
        
        if operation in ('-', '*', '/') and (left_type == 'str' or right_type == 'str'):
            suggestions.append(
                f"Arithmetic operations require numbers. "
                f"Use int() or float() to convert: int(value)"
            )
        
        return suggestions
    
    def _find_similar_names(self, target, candidates, threshold=2):
        """查找相似的名称"""
        import difflib
        matches = difflib.get_close_matches(target, candidates, n=3, cutoff=0.6)
        return matches
    
    def get_quick_fix(self, error):
        """获取快速修复代码"""
        quick_fixes = {
            'HPLNameError': self._fix_name_error,
            'HPLTypeError': self._fix_type_error,
        }
        
        fixer = quick_fixes.get(error.__class__.__name__)
        if fixer:
            return fixer(error)
        return None
    
    def _fix_name_error(self, error):
        """生成变量名错误的修复建议"""
        # 解析错误消息获取变量名
        import re
        match = re.search(r"'(\w+)'", str(error))
        if match:
            var_name = match.group(1)
            return f"# 添加变量定义\n{var_name} = null  # 或适当的初始值"
        return None
    
    def _fix_type_error(self, error):
        """生成类型错误的修复建议"""
        # 根据错误消息生成修复
        if "Cannot add" in str(error):
            return "# 使用类型转换\nresult = str(left) + str(right)"
        return None
```

```python
# 集成到错误格式化
def format_error_for_user(error, source_code=None, suggestion_engine=None):
    # ... 现有代码 ...
    
    # 添加智能建议
    if suggestion_engine:
        suggestions = []
        
        if isinstance(error, HPLNameError):
            suggestions = suggestion_engine.suggest_for_name_error(
                extract_var_name(error)
            )
        elif isinstance(error, HPLTypeError):
            suggestions = suggestion_engine.suggest_for_type_error(
                extract_operation(error),
                extract_left_type(error),
                extract_right_type(error)
            )
        
        if suggestions:
            lines.append("\n   💡 建议:")
            for i, suggestion in enumerate(suggestions, 1):
                lines.append(f"      {i}. {suggestion}")
        
        # 添加快速修复代码
        quick_fix = suggestion_engine.get_quick_fix(error)
        if quick_fix:
            lines.append(f"\n   🛠️  快速修复:\n{quick_fix}")
    
    return '\n'.join(lines)
```

---

### 2.7 错误聚合与批量报告（优先级：低）

#### 建议改进：多错误收集

```python
# 新增 error_collector.py
class HPLErrorCollector:
    """错误收集器 - 支持收集多个错误后继续执行"""
    
    def __init__(self, max_errors=10):
        self.errors = []
        self.warnings = []
        self.max_errors = max_errors
        self._should_stop = False
    
    def add_error(self, error, severity='error'):
        """添加错误"""
        if severity == 'error':
            self.errors.append(error)
            if len(self.errors) >= self.max_errors:
                self._should_stop = True
        else:
            self.warnings.append(error)
    
    def has_errors(self):
        return len(self.errors) > 0
    
    def should_stop(self):
        return self._should_stop
    
    def generate_report(self):
        """生成批量错误报告"""
        lines = ["=" * 60, "错误报告", "=" * 60]
        
        if self.warnings:
            lines.append(f"\n⚠️  警告 ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
        
        if self.errors:
            lines.append(f"\n❌ 错误 ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                lines.append(f"\n  {i}. {error.__class__.__name__}")
                lines.append(f"     {error}")
        
        lines.append("\n" + "=" * 60)
        return '\n'.join(lines)
```

---

### 2.8 模块导入错误增强（优先级：中）

#### 建议改进

```python
# 改进模块加载错误
def execute_import(self, stmt, local_scope):
    """执行 import 语句（增强版）"""
    module_name = stmt.module_name
    alias = stmt.alias or module_name
    
    # 检查循环导入
    if module_name in self._import_stack:
        cycle = ' -> '.join(self._import_stack + [module_name])
        raise HPLImportError(
            f"Circular import detected: {cycle}",
            line=stmt.line,
            column=stmt.column,
            error_key='IMPORT_CIRCULAR'
        )
    
    try:
        self._import_stack.append(module_name)
        module = load_module(module_name)
        self._import_stack.pop()
        
        if module:
            self.imported_modules[alias] = module
            local_scope[alias] = module
            return None
        
    except ImportError as e:
        # 分析导入失败原因
        suggestions = self._analyze_import_failure(module_name, e)
        
        raise HPLImportError(
            f"Cannot import module '{module_name}': {e}",
            line=stmt.line,
            column=stmt.column,
            context=f"Suggestions: {suggestions}" if suggestions else None,
            error_key='IMPORT_MODULE_NOT_FOUND',
            original_error=e
        ) from e
    
    raise HPLImportError(
        f"Module '{module_name}' not found",
        line=stmt.line,
        column=stmt.column,
        error_key='IMPORT_MODULE_NOT_FOUND'
    )

def _analyze_import_failure(self, module_name, error):
    """分析导入失败原因并提供建议"""
    suggestions = []
    
    # 检查是否是标准库模块
    stdlib_modules = ['io', 'math', 'time', 'os', 'json']
    if module_name in stdlib_modules:
        suggestions.append(f"'{module_name}' is a standard library module")
    
    # 检查是否是拼写错误
    available_modules = get_available_modules()  # 需要实现
    similar = difflib.get_close_matches(module_name, available_modules, n=2)
    if similar:
        suggestions.append(f"Did you mean: {', '.join(similar)}?")
    
    # 检查 Python 依赖
    if "No module named" in str(error):
        suggestions.append(
            f"Python module not found. Try: pip install {module_name}"
        )
    
    return suggestions
```

---

## 3. 实施路线图

### 阶段 1：核心改进（1-2 周）
- [ ] 实现统一的 HPLErrorHandler
- [ ] 增强错误上下文捕获
- [ ] 完善错误代码系统

### 阶段 2：开发者体验（2-3 周）
- [ ] 实现智能建议引擎
- [ ] 增强错误消息（边界检查、类型提示）
- [ ] 添加快速修复代码生成

### 阶段 3：高级特性（3-4 周）
- [ ] 实现 finally 块支持
- [ ] 多 catch 子句支持
- [ ] 错误聚合器

### 阶段 4：文档与优化（1 周）
- [ ] 编写错误代码文档
- [ ] 创建错误解决指南
- [ ] 性能优化

---

## 4. 代码示例：改进后的完整错误处理

```python
# 改进后的 evaluator.py 错误处理片段
class HPLEvaluator:
    def __init__(self, ...):
        # ... 现有初始化 ...
        self.error_context = ErrorContextManager(self)
    
    def execute_statement(self, stmt, local_scope):
        try:
            return self._execute_statement_impl(stmt, local_scope)
        except HPLRuntimeError as e:
            # 自动增强错误上下文
            self.error_context.enhance(e, stmt, local_scope)
            raise
        except Exception as e:
            # 包装未预期错误
            wrapped = self.error_context.wrap_unexpected(e, stmt)
            raise wrapped from e
    
    def _execute_statement_impl(self, stmt, local_scope):
        # 原有实现移到此处
        ...
```

---

## 5. 总结

HPL 运行时的错误处理系统已经具备了良好的基础架构，通过实施本报告中的改进建议，可以显著提升：

1. **错误恢复能力** - 支持 finally 和多 catch
2. **调试效率** - 丰富的上下文信息和智能建议
3. **开发者体验** - 清晰的错误消息和快速修复
4. **系统稳定性** - 统一的错误处理和更好的边缘情况覆盖

建议优先实施 **错误恢复机制** 和 **开发者体验改进**，这两项改进将直接提升用户的开发效率。

---

*报告生成时间: 2024*
*分析范围: HPL Runtime v1.x*
*修正说明: 已修正 HPL 语法示例，使用正确的 YAML 格式（冒号+缩进）*
