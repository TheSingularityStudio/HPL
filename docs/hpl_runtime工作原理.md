# HPL Runtime 工作原理文档

> 本文档详细阐述 `hpl_runtime` 模块的内部架构、工作流程和实现细节，供 IDE 开发参考。

## 目录

1. [整体架构概述](#1-整体架构概述)
2. [核心组件详解](#2-核心组件详解)
3. [模块系统架构](#3-模块系统架构)
4. [数据模型](#4-数据模型)
5. [执行流程示例](#5-执行流程示例)
6. [IDE 开发关键信息](#6-ide-开发关键信息)

---

## 1. 整体架构概述

### 1.1 解释器三阶段架构

`hpl_runtime` 采用经典的三阶段解释器架构：

```
┌─────────────────────────────────────────────────────────────┐
│                      HPL 源代码 (.hpl)                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段1: 词法分析 (Lexer)                                      │
│  - 输入: 源代码字符串                                         │
│  - 输出: Token 序列                                          │
│  - 关键类: HPLLexer, Token                                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段2: 语法解析 (Parser)                                     │
│  - 输入: Token 序列                                           │
│  - 输出: AST (抽象语法树)                                     │
│  - 关键类: HPLParser, HPLASTParser                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  阶段3: 执行 (Evaluator)                                      │
│  - 输入: AST + 运行时环境                                     │
│  - 输出: 执行结果                                            │
│  - 关键类: HPLEvaluator                                       │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块依赖关系

```
hpl_runtime/
├── __init__.py          # 包入口，导出主要类
├── interpreter.py       # CLI入口，协调parser和evaluator
├── lexer.py            # 词法分析（无依赖）
├── parser.py           # 顶层解析（依赖: yaml, lexer, ast_parser, models）
├── ast_parser.py       # AST构建（依赖: models）
├── evaluator.py        # 代码执行（依赖: models, module_loader）
├── models.py           # 数据模型（无依赖）
├── module_base.py      # 模块基类（无依赖）
├── module_loader.py    # 模块加载（依赖: module_base, stdlib）
├── package_manager.py  # 包管理CLI（依赖: module_loader）
└── stdlib/             # 标准库实现
    ├── io.py
    ├── math.py
    ├── json_mod.py
    ├── os_mod.py
    └── time_mod.py
```

### 1.3 数据流向

```
HPL文件 → YAML解析 → 函数预处理 → 类/对象/函数定义
                                    ↓
                              函数体字符串
                                    ↓
                              Lexer.tokenize()
                                    ↓
                              Token列表
                                    ↓
                              ASTParser.parse_block()
                                    ↓
                              AST节点树
                                    ↓
                              Evaluator.execute_function()
                                    ↓
                              执行结果
```

---

## 2. 核心组件详解

### 2.1 词法分析器 (lexer.py)

#### 2.1.1 Token 类

```python
class Token:
    def __init__(self, type, value, line=0, column=0):
        self.type = type      # Token类型
        self.value = value    # Token值
        self.line = line      # 行号（从1开始）
        self.column = column  # 列号（从0开始）
```

**Token 类型列表：**

| 类型 | 示例 | 说明 |
|------|------|------|
| `NUMBER` | `42`, `3.14` | 整数或浮点数 |
| `STRING` | `"hello"` | 字符串字面量 |
| `BOOLEAN` | `true`, `false` | 布尔值 |
| `IDENTIFIER` | `foo`, `bar` | 标识符 |
| `KEYWORD` | `if`, `for`, `return` | 关键字 |
| `PLUS` | `+` | 加号 |
| `MINUS` | `-` | 减号 |
| `MUL` | `*` | 乘号 |
| `DIV` | `/` | 除号 |
| `MOD` | `%` | 取模 |
| `ASSIGN` | `=` | 赋值 |
| `EQ` | `==` | 等于 |
| `NE` | `!=` | 不等于 |
| `LT` | `<` | 小于 |
| `LE` | `<=` | 小于等于 |
| `GT` | `>` | 大于 |
| `GE` | `>=` | 大于等于 |
| `AND` | `&&` | 逻辑与 |
| `OR` | `\|\|` | 逻辑或 |
| `NOT` | `!` | 逻辑非 |
| `INCREMENT` | `++` | 自增 |
| `LPAREN` | `(` | 左括号 |
| `RPAREN` | `)` | 右括号 |
| `LBRACE` | `{` | 左花括号 |
| `RBRACE` | `}` | 右花括号 |
| `LBRACKET` | `[` | 左方括号 |
| `RBRACKET` | `]` | 右方括号 |
| `SEMICOLON` | `;` | 分号 |
| `COMMA` | `,` | 逗号 |
| `DOT` | `.` | 点号 |
| `COLON` | `:` | 冒号 |
| `ARROW` | `=>` | 箭头（函数定义） |
| `INDENT` | - | 缩进增加 |
| `DEDENT` | - | 缩进减少 |
| `EOF` | - | 文件结束 |

#### 2.1.2 HPLLexer 类

**核心属性：**

```python
class HPLLexer:
    def __init__(self, text):
        self.text = text           # 源代码
        self.pos = 0               # 当前位置
        self.current_char = ...    # 当前字符
        self.line = 1              # 当前行号
        self.column = 0            # 当前列号
        self.indent_stack = [0]    # 缩进栈（用于Python式缩进）
        self.at_line_start = True  # 是否在行首
```

**关键方法：**

| 方法 | 功能 |
|------|------|
| `tokenize()` | 主入口，返回Token列表 |
| `advance()` | 移动到下一个字符 |
| `peek()` | 查看下一个字符（不移动） |
| `skip_whitespace()` | 跳过空白字符 |
| `skip_comment()` | 跳过注释（# 到行尾） |
| `number()` | 解析数字（整数/浮点数） |
| `string()` | 解析字符串（支持转义序列） |
| `identifier()` | 解析标识符/关键字 |

#### 2.1.3 缩进跟踪机制

HPL 支持 Python 式的缩进敏感语法，Lexer 通过 `indent_stack` 实现：

```python
# 示例代码
if (x > 0) {
    echo("positive")
    if (x > 10) {
        echo("large")
    }
}

# 生成的Token序列（简化）
# KEYWORD(if), LPAREN, IDENTIFIER(x), GT, NUMBER(0), RPAREN, LBRACE
# INDENT(4)
# IDENTIFIER(echo), LPAREN, STRING("positive"), RPAREN
# INDENT(8)
# IDENTIFIER(echo), LPAREN, STRING("large"), RPAREN
# DEDENT(4)
# DEDENT(0)
# RBRACE
```

**缩进处理流程：**

1. 遇到行首空白字符时，计算缩进级别
2. 与 `indent_stack[-1]` 比较：
   - 更大 → 生成 `INDENT`，压入栈
   - 更小 → 生成 `DEDENT`，弹出栈直到匹配
3. 文件结束时，弹出所有剩余缩进级别

---

### 2.2 顶层解析器 (parser.py)

#### 2.2.1 HPLParser 类

**核心职责：**
- 加载和解析 HPL 文件（YAML 格式）
- 预处理函数定义（箭头函数语法转换）
- 处理文件包含（includes）
- 解析类、对象、函数定义

**解析流程：**

```python
def __init__(self, hpl_file):
    self.hpl_file = hpl_file
    self.classes = {}      # 类定义字典
    self.objects = {}      # 对象实例字典
    self.main_func = None  # main函数
    self.call_target = None
    self.imports = []      # 导入语句
    self.data = self.load_and_parse()

def load_and_parse(self):
    # 1. 读取文件内容
    # 2. 预处理函数定义（将 => 语法转换为 YAML 字面量块）
    # 3. 使用 yaml.safe_load() 解析
    # 4. 处理 includes 文件包含
    # 5. 返回解析后的数据结构
```

#### 2.2.2 函数预处理机制

HPL 使用箭头函数语法定义方法，但需要转换为 YAML 兼容格式：

```yaml
# 原始 HPL 代码
methods:
  add: (a, b) => {
    return a + b
  }
  multiply: (x, y) => {
    result = x * y
    return result
  }
```

**预处理转换：**

```python
def preprocess_functions(self, content):
    # 检测函数定义行（包含 =>）
    # 收集完整的函数体（匹配花括号）
    # 转换为 YAML 字面量块格式（使用 |）
```

**转换后：**

```yaml
methods:
  add: |
    (a, b) => {
      return a + b
    }
  multiply: |
    (x, y) => {
      result = x * y
      return result
    }
```

#### 2.2.3 文件包含处理（改进版）

**`_resolve_include_path()` 方法**

支持多路径搜索的 include 文件解析：

```python
def _resolve_include_path(self, include_file):
    """
    解析include文件路径，支持多种路径格式：
    1. 绝对路径（Unix: /path, Windows: C:\path）
    2. 相对当前文件目录
    3. 相对当前工作目录
    4. HPL_MODULE_PATHS中的路径
    """
    include_path = Path(include_file)
    
    # 1. 检查是否为绝对路径
    if include_path.is_absolute():
        if include_path.exists():
            return str(include_path)
        return None
    
    # 获取当前HPL文件所在目录
    current_dir = Path(self.hpl_file).parent.resolve()
    
    # 2. 相对当前文件目录
    resolved_path = current_dir / include_path
    if resolved_path.exists():
        return str(resolved_path)
    
    # 3. 相对当前工作目录
    cwd_path = Path.cwd() / include_path
    if cwd_path.exists():
        return str(cwd_path)
    
    # 4. HPL_MODULE_PATHS中的路径
    for search_path in HPL_MODULE_PATHS:
        module_path = Path(search_path) / include_path
        if module_path.exists():
            return str(module_path)
    
    return None
```

**路径解析优先级：**
1. 绝对路径（直接解析）
2. 相对当前文件目录（如 `subdir/utils.hpl`）
3. 相对当前工作目录
4. HPL_MODULE_PATHS 中的路径（标准库和用户库目录）

**`merge_data()` 方法**

合并 include 文件数据到主数据，支持类、对象、函数和导入：

```python
def merge_data(self, main_data, include_data):
    """合并include数据到主数据，支持classes、objects、functions、imports"""
    reserved_keys = {'includes', 'imports', 'classes', 'objects', 'call'}
    
    # 合并字典类型的数据（classes, objects）
    for key in ['classes', 'objects']:
        if key in include_data:
            if key not in main_data:
                main_data[key] = {}
            if isinstance(include_data[key], dict):
                main_data[key].update(include_data[key])
    
    # 合并函数定义（HPL中函数是顶层键值对，值包含'=>'）
    for key, value in include_data.items():
        if key not in reserved_keys:
            # 检查是否是函数定义（包含 =>）
            if isinstance(value, str) and '=>' in value:
                # 只合并主数据中不存在的函数（避免覆盖）
                if key not in main_data:
                    main_data[key] = value
    
    # 合并imports
    if 'imports' in include_data:
        if 'imports' not in main_data:
            main_data['imports'] = []
        if isinstance(include_data['imports'], list):
            main_data['imports'].extend(include_data['imports'])
```

#### 2.2.4 顶层函数解析

**`parse_top_level_functions()` 方法**

解析 YAML 根级别的所有函数定义（包括 `main` 和其他自定义函数）：

```python
def parse_top_level_functions(self):
    """解析所有顶层函数定义"""
    # 预定义的保留键，不是函数
    reserved_keys = {'includes', 'imports', 'classes', 'objects', 'call'}
    
    for key, value in self.data.items():
        if key in reserved_keys:
            continue
        
        # 检查值是否是函数定义（包含 =>）
        if isinstance(value, str) and '=>' in value:
            func = self.parse_function(value)
            self.functions[key] = func
            
            # 特别处理 main 函数
            if key == 'main':
                self.main_func = func
```


**`_parse_call_expression()` 方法**

解析 `call:` 指令中的函数调用表达式，支持带参数的调用：

```python
def _parse_call_expression(self, call_str):
    """解析 call 表达式，提取函数名和参数"""
    call_str = call_str.strip()
    
    # 查找左括号
    if '(' in call_str:
        func_name = call_str[:call_str.find('(')].strip()
        args_str = call_str[call_str.find('(')+1:call_str.rfind(')')].strip()
        
        # 解析参数
        args = []
        if args_str:
            # 按逗号分割参数
            for arg in args_str.split(','):
                arg = arg.strip()
                # 尝试解析为整数
                try:
                    args.append(int(arg))
                except ValueError:
                    # 尝试解析为浮点数
                    try:
                        args.append(float(arg))
                    except ValueError:
                        # 作为字符串处理（去掉引号）
                        if (arg.startswith('"') and arg.endswith('"')) or \
                           (arg.startswith("'") and arg.endswith("'")):
                            args.append(arg[1:-1])
                        else:
                            args.append(arg)  # 变量名或其他
        
        return func_name, args
    else:
        # 没有括号，如 call: main
        return call_str, []
```

#### 2.2.4 函数体解析

```python
def parse_function(self, func_str):
    # 解析箭头函数语法: (params) => { body }
    # 1. 提取参数列表
    # 2. 提取函数体
    # 3. 使用 Lexer 和 ASTParser 解析函数体
    # 4. 返回 HPLFunction 对象
```


---

### 2.3 AST 解析器 (ast_parser.py)

#### 2.3.1 HPLASTParser 类

**核心职责：**
- 将 Token 序列解析为 AST 节点
- 实现表达式优先级解析（ Pratt Parser 风格）
- 支持多种语句类型

**表达式优先级（从高到低）：**

```
1.  primary: 字面量、变量、括号表达式、数组字面量
2.  postfix: 数组访问、后缀自增、方法调用
3.  unary: 前缀自增、逻辑非、负号
4.  multiplicative: *, /, %
5.  additive: +, -
6.  comparison: <, <=, >, >=
7.  equality: ==, !=
8.  logical_and: &&
9.  logical_or: ||
```

#### 2.3.2 表达式解析方法

```python
def parse_expression(self):
    return self.parse_or()  # 从最低优先级开始

def parse_or(self):
    left = self.parse_and()
    while current_token is OR:
        advance()
        right = self.parse_and()
        left = BinaryOp(left, '||', right)
    return left

# 类似地: parse_and, parse_equality, parse_comparison,
# parse_additive, parse_multiplicative, parse_unary, parse_primary
```

#### 2.3.3 语句解析

**支持的语句类型：**

| 语句 | 解析方法 | AST节点类 |
|------|----------|-----------|
| 赋值 | `parse_statement()` | `AssignmentStatement` |
| 数组赋值 | `parse_statement()` | `ArrayAssignmentStatement` |
| 返回 | `parse_statement()` | `ReturnStatement` |
| 自增 | `parse_statement()` | `IncrementStatement` |
| 条件 | `parse_if_statement()` | `IfStatement` |
| 循环 | `parse_for_statement()` | `ForStatement` |
| While | `parse_while_statement()` | `WhileStatement` |
| 异常处理 | `parse_try_catch_statement()` | `TryCatchStatement` |
| 输出 | `parse_statement()` | `EchoStatement` |
| 导入 | `parse_import_statement()` | `ImportStatement` |
| 跳出 | `parse_statement()` | `BreakStatement` |
| 继续 | `parse_statement()` | `ContinueStatement` |

#### 2.3.4 块解析（多语法支持）

HPL 支持多种代码块语法：

```python
def parse_block(self):
    # 情况1: 以 INDENT 开始（Python式缩进）
    if current_token is INDENT:
        expect(INDENT)
        statements = parse_statements_until_dedent()
        expect(DEDENT)
    
    # 情况2: 以花括号开始（C风格）
    elif current_token is LBRACE:
        expect(LBRACE)
        while not RBRACE:
            statements.append(parse_statement())
        expect(RBRACE)
    
    # 情况3: 以冒号开始（YAML风格）
    elif current_token is COLON:
        expect(COLON)
        if INDENT:
            # 多行缩进块
        else:
            # 单行语句
```

---

### 2.4 代码执行器 (evaluator.py)

#### 2.4.1 HPLEvaluator 类

**核心属性：**

```python
class HPLEvaluator:
    def __init__(self, classes, objects, functions=None, main_func=None, 
                 call_target=None, call_args=None):
        self.classes = classes           # 类定义字典
        self.objects = objects             # 全局对象字典
        self.functions = functions or {}   # 所有顶层函数
        self.main_func = main_func         # main函数
        self.call_target = call_target     # 调用目标
        self.call_args = call_args or []   # call 调用的参数
        self.global_scope = objects        # 全局作用域
        self.current_obj = None            # 当前对象（this绑定）
        self.call_stack = []               # 调用栈（错误跟踪）
        self.imported_modules = {}         # 导入的模块
```

**`run()` 方法 - 执行入口：**

```python
def run(self):
    """
    执行入口函数。
    
    支持两种调用方式：
    1. 通过 call: 指令指定函数名和参数，如 call: add(5, 3)
    2. 默认执行 main 函数（如果存在）
    """
    # 如果指定了 call_target，执行对应的函数
    if self.call_target:
        # 首先尝试从 functions 字典中查找
        if self.call_target in self.functions:
            target_func = self.functions[self.call_target]
            # 构建参数作用域，将 call_args 绑定到函数参数
            local_scope = {}
            for i, param in enumerate(target_func.params):
                if i < len(self.call_args):
                    local_scope[param] = self.call_args[i]
                else:
                    local_scope[param] = None  # 默认值为 None
            self.execute_function(target_func, local_scope)
        elif self.call_target == 'main' and self.main_func:
            self.execute_function(self.main_func, {})
        else:
            raise ValueError(f"Unknown call target: {self.call_target}")
    elif self.main_func:
        self.execute_function(self.main_func, {})
```


#### 2.4.2 表达式求值

```python
def evaluate_expression(self, expr, local_scope):
    if isinstance(expr, IntegerLiteral):
        return expr.value
    elif isinstance(expr, StringLiteral):
        return expr.value
    elif isinstance(expr, Variable):
        return self._lookup_variable(expr.name, local_scope)
    elif isinstance(expr, BinaryOp):
        left = evaluate_expression(expr.left, local_scope)
        right = evaluate_expression(expr.right, local_scope)
        return self._eval_binary_op(left, expr.op, right)
    elif isinstance(expr, FunctionCall):
        return self._call_builtin_function(expr, local_scope)
    elif isinstance(expr, MethodCall):
        return self._call_method(expr, local_scope)
    # ... 其他表达式类型
```

#### 2.4.3 语句执行

```python
def execute_statement(self, stmt, local_scope):
    if isinstance(stmt, AssignmentStatement):
        value = evaluate_expression(stmt.expr, local_scope)
        local_scope[stmt.var_name] = value
    
    elif isinstance(stmt, ReturnStatement):
        value = evaluate_expression(stmt.expr, local_scope)
        return ReturnValue(value)  # 包装返回值
    
    elif isinstance(stmt, IfStatement):
        cond = evaluate_expression(stmt.condition, local_scope)
        if cond:
            return execute_block(stmt.then_block, local_scope)
        elif stmt.else_block:
            return execute_block(stmt.else_block, local_scope)
    
    elif isinstance(stmt, ForStatement):
        execute_statement(stmt.init, local_scope)
        while evaluate_expression(stmt.condition, local_scope):
            try:
                result = execute_block(stmt.body, local_scope)
                if isinstance(result, ReturnValue):
                    return result
            except BreakException:
                break
            except ContinueException:
                pass
            evaluate_expression(stmt.increment_expr, local_scope)
    
    # ... 其他语句类型
```

#### 2.4.4 作用域管理

```python
def _lookup_variable(self, name, local_scope):
    """变量查找顺序: 局部作用域 → 全局作用域"""
    if name in local_scope:
        return local_scope[name]
    elif name in self.global_scope:
        return self.global_scope[name]
    else:
        raise ValueError(f"Undefined variable: '{name}'")

def _update_variable(self, name, value, local_scope):
    """变量更新: 存在则更新，否则创建局部变量"""
    if name in local_scope:
        local_scope[name] = value
    elif name in self.global_scope:
        self.global_scope[name] = value
    else:
        local_scope[name] = value  # 默认创建局部变量
```

#### 2.4.5 方法调用机制

```python
def _call_method(self, obj, method_name, args):
    # 1. 查找方法（当前类 → 父类）
    method = find_method(obj.hpl_class, method_name)
    
    # 2. 设置 this 绑定
    prev_obj = self.current_obj
    self.current_obj = obj
    
    # 3. 创建方法作用域
    method_scope = {
        param: args[i] for i, param in enumerate(method.params)
    }
    method_scope['this'] = obj
    
    # 4. 添加到调用栈
    self.call_stack.append(f"{obj.name}.{method_name}()")
    
    try:
        # 5. 执行方法
        result = self.execute_function(method, method_scope)
    finally:
        # 6. 恢复状态
        self.call_stack.pop()
        self.current_obj = prev_obj
    
    return result
```

#### 2.4.6 内置函数与用户定义函数

**内置函数：**

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `echo(msg)` | 任意 | None | 打印输出 |
| `len(obj)` | list/str | int | 长度 |
| `int(x)` | 任意 | int | 转整数 |
| `str(x)` | 任意 | str | 转字符串 |
| `type(x)` | 任意 | str | 类型名称 |
| `abs(x)` | number | number | 绝对值 |
| `max(...)` | numbers | number | 最大值 |
| `min(...)` | numbers | number | 最小值 |
| `input(prompt?)` | str（可选） | str | 获取用户输入，可选提示信息 |

**用户定义函数调用：**

通过 include 导入的函数或主文件中定义的顶层函数可以直接调用：

```python
# 在 evaluate_expression() 中处理 FunctionCall
elif isinstance(expr, FunctionCall):
    # 内置函数处理...
    
    else:
        # 检查是否是用户定义的函数（从include或其他方式导入）
        if expr.func_name in self.functions:
            # 调用用户定义的函数
            target_func = self.functions[expr.func_name]
            args = [self.evaluate_expression(arg, local_scope) for arg in expr.args]
            # 构建参数作用域
            func_scope = {}
            for i, param in enumerate(target_func.params):
                if i < len(args):
                    func_scope[param] = args[i]
                else:
                    func_scope[param] = None  # 默认值为 None
            return self.execute_function(target_func, func_scope)
        else:
            raise ValueError(f"Unknown function {expr.func_name}")
```



---

## 3. 模块系统架构

### 3.1 模块加载优先级

`module_loader.py` 实现了四层模块加载机制：

```
优先级1: 标准库模块 (stdlib)
    └── io, math, json, os, time
    
优先级2: Python 第三方包 (PyPI)
    └── 通过 pip 安装，自动包装为 HPLModule
    
优先级3: 本地 HPL 模块 (.hpl)
    └── 当前目录 / HPL_PACKAGES_DIR / 自定义路径
    
优先级4: 本地 Python 模块 (.py)
    └── 当前目录 / HPL_PACKAGES_DIR / 自定义路径
```

### 3.2 HPLModule 基类

```python
class HPLModule:
    def __init__(self, name, description=""):
        self.name = name
        self.description = description
        self.functions = {}    # 函数名 -> {func, param_count, description}
        self.constants = {}    # 常量名 -> {value, description}
    
    def register_function(self, name, func, param_count=None, description="")
    def register_constant(self, name, value, description="")
    def call_function(self, func_name, args)
    def get_constant(self, name)
```

### 3.3 标准库实现模式

以 `math` 模块为例：

```python
# 1. 导入基类
from hpl_runtime.module_base import HPLModule

# 2. 实现函数
def sqrt(x):
    if not isinstance(x, (int, float)):
        raise TypeError(f"sqrt() requires number, got {type(x).__name__}")
    return math.sqrt(x)

# 3. 创建模块实例
module = HPLModule('math', 'Mathematical functions')

# 4. 注册函数和常量
module.register_function('sqrt', sqrt, 1, 'Square root')
module.register_constant('PI', math.pi, 'Pi constant')
```

### 3.4 模块搜索路径

```python
HPL_MODULE_PATHS = [
    Path.home() / '.hpl' / 'packages',  # 默认包目录
    # 可通过 add_module_path() 添加自定义路径
]

# 搜索顺序：
# 1. 当前 HPL 文件所在目录
# 2. 当前工作目录
# 3. HPL_MODULE_PATHS
# 4. 调用时指定的搜索路径
```

### 3.5 Include 文件搜索路径

Include 文件使用与模块加载类似的多路径搜索机制：

```
搜索优先级：
1. 绝对路径（Unix: /path/to/file.hpl, Windows: C:\path\to\file.hpl）
2. 相对当前文件目录（如 subdir/utils.hpl）
3. 相对当前工作目录
4. HPL_MODULE_PATHS 中的路径
```

**示例：**
```yaml
# 同级目录
includes:
  - utils.hpl

# 子目录
includes:
  - lib/helpers.hpl

# 父目录
includes:
  - ../common.hpl
```


---

## 4. 数据模型

### 4.1 AST 节点类层次

```
Expression (表达式基类)
├── IntegerLiteral (整数字面量)
├── FloatLiteral (浮点数字面量)
├── StringLiteral (字符串字面量)
├── BooleanLiteral (布尔字面量)
├── BinaryOp (二元运算: left op right)
├── UnaryOp (一元运算: op operand)
├── Variable (变量引用)
├── FunctionCall (函数调用)
├── MethodCall (方法调用: obj.method(args))
├── PostfixIncrement (后缀自增)
├── ArrayLiteral (数组字面量: [1, 2, 3])
└── ArrayAccess (数组访问: arr[index])

Statement (语句基类)
├── AssignmentStatement (赋值: var = expr)
├── ArrayAssignmentStatement (数组赋值: arr[i] = expr)
├── ReturnStatement (返回: return expr)
├── IncrementStatement (自增: ++var)
├── BlockStatement (语句块: { ... })
├── IfStatement (条件: if (cond) { ... } else { ... })
├── ForStatement (for循环: for (init; cond; inc) { ... })
├── WhileStatement (while循环: while (cond) { ... })
├── TryCatchStatement (异常: try { ... } catch (e) { ... })
├── EchoStatement (输出: echo(expr))
├── ImportStatement (导入: import module [as alias])
├── BreakStatement (跳出循环)
└── ContinueStatement (继续循环)
```

### 4.2 运行时对象

```python
class HPLClass:
    def __init__(self, name, methods, parent=None):
        self.name = name           # 类名
        self.methods = methods     # 方法字典: {name: HPLFunction}
        self.parent = parent       # 父类名（可选）

class HPLObject:
    def __init__(self, name, hpl_class, attributes=None):
        self.name = name           # 对象名
        self.hpl_class = hpl_class # 所属类 (HPLClass)
        self.attributes = attributes or {}  # 实例属性

class HPLFunction:
    def __init__(self, params, body):
        self.params = params       # 参数名列表
        self.body = body           # 函数体 AST (BlockStatement)
```

---

## 5. 执行流程示例

### 5.1 完整执行流程

#### 示例1: 调用 main 函数

以以下 HPL 代码为例：

```yaml
classes:
  Calculator:
    methods:
      add: (a, b) => {
        result = a + b
        return result
      }

objects:
  calc: Calculator()

main: () => {
  x = 10
  y = 20
  sum = calc.add(x, y)
  echo("Result: " + sum)
}

call: main
```

#### 示例2: 调用任意顶层函数（带参数）

```yaml
# 定义顶层函数
add: (a, b) => {
    result = a + b
    echo("Adding " + a + " + " + b + " = " + result)
    return result
  }

greet: (name) => {
    message = "Hello, " + name + "!"
    echo message
    return message
  }

# 调用 add 函数并传递参数
call: add(5, 3)
```

**执行步骤（call: add(5, 3)）：**

```
1. HPLParser 解析 call 表达式
   └── _parse_call_expression("add(5, 3)")
       ├── 提取函数名: "add"
       └── 解析参数: [5, 3]（整数列表）

2. HPLEvaluator 初始化
   ├── classes = {}
   ├── objects = {}
   ├── functions = {"add": HPLFunction, "greet": HPLFunction}
   ├── main_func = None
   ├── call_target = "add"
   └── call_args = [5, 3]

3. run() 方法执行
   └── 发现 call_target="add" 在 functions 中
       └── 构建局部作用域: {a: 5, b: 3}
           └── execute_function(add_function, {a: 5, b: 3})
               ├── AssignmentStatement(result = a + b) → result = 8
               ├── EchoStatement("Adding 5 + 3 = 8") → 输出
               └── ReturnStatement(result) → 返回 8
```


**执行步骤：**

```
1. interpreter.py 接收命令行参数
   └── python interpreter.py example.hpl

2. 设置当前 HPL 文件路径
   └── set_current_hpl_file("example.hpl")

3. HPLParser 解析文件
   ├── load_and_parse()
   │   ├── 读取文件内容
   │   ├── preprocess_functions() 转换箭头函数
   │   ├── yaml.safe_load() 解析 YAML
   │   └── 处理 includes
   └── parse()
       ├── parse_classes() 解析类定义
       ├── parse_objects() 解析对象实例
       └── parse_function() 解析 main 函数

4. HPLEvaluator 执行
   ├── 初始化: classes, objects, main_func, call_target
   ├── 处理顶层 imports
   └── run()
       └── execute_function(main_func, {})
           └── execute_block(main_func.body, {})
               ├── execute_statement(AssignmentStatement(x=10))
               ├── execute_statement(AssignmentStatement(y=20))
               ├── execute_statement(MethodCall(calc.add))
               │   └── _call_method(calc, "add", [10, 20])
               │       ├── 创建方法作用域: {a: 10, b: 20, this: calc}
               │       ├── execute_function(add_method, method_scope)
               │       │   ├── AssignmentStatement(result = a + b)
               │       │   └── ReturnStatement(result)
               │       └── 返回 30
               ├── AssignmentStatement(sum = 30)
               └── EchoStatement("Result: 30")
                   └── 输出: Result: 30
```

---

## 6. IDE 开发关键信息

### 6.1 Token 位置信息

所有 Token 都包含精确的位置信息，可用于 IDE 的语法高亮和错误定位：

```python
token.line    # 行号（从1开始）
token.column  # 列号（从0开始）
```

**错误信息格式：**

```python
# Lexer 错误
f"Invalid character '{char}' at line {line}, column {column}"

# Parser 错误
f"Expected {type}, got {token} at line {token.line}, column {token.column}"
f"Expected keyword {value}, got {token} at line {token.line}, column {token.column}"
```

### 6.2 错误处理机制

| 错误类型 | 抛出位置 | 捕获位置 | 处理方式 |
|----------|----------|----------|----------|
| 词法错误 | Lexer | interpreter.py | 打印错误，退出码1 |
| 语法错误 | Parser/ASTParser | interpreter.py | 打印错误，退出码1 |
| 运行时错误 | Evaluator | interpreter.py | 打印错误，退出码1 |
| 用户异常 | Evaluator (try-catch) | Evaluator | 存储到 catch 变量 |
| Break | Evaluator | For/While 循环 | 跳出循环 |
| Continue | Evaluator | For/While 循环 | 继续下一次迭代 |
| Return | Evaluator | 函数调用链 | 向上传播返回值 |

### 6.3 调用栈跟踪

```python
self.call_stack = []  # 调用栈列表

# 方法调用时压入
self.call_stack.append(f"{obj.name}.{method_name}()")

# 方法返回时弹出
self.call_stack.pop()

# 可用于错误报告
" → ".join(self.call_stack)  # 调用链显示
```

### 6.4 扩展点

**1. 添加新的内置函数：**

在 `evaluator.py` 的 `evaluate_expression()` 中 `FunctionCall` 处理部分添加：

```python
elif expr.func_name == 'new_func':
    arg = self.evaluate_expression(expr.args[0], local_scope)
    return new_func_impl(arg)
```

**2. 添加新的标准库模块：**

1. 在 `stdlib/` 创建新模块文件（如 `string_mod.py`）
2. 实现函数并创建 `HPLModule` 实例
3. 在 `module_loader.py` 的 `init_stdlib()` 中注册

**3. 自定义模块加载：**

```python
from hpl_runtime.module_loader import add_module_path

# 添加自定义模块搜索路径
add_module_path("/path/to/custom/modules")
```

### 6.5 关键数据结构速查

**Token 结构：**
```python
{
    'type': 'IDENTIFIER',  # 字符串
    'value': 'foo',        # 任意类型
    'line': 10,            # 整数
    'column': 5            # 整数
}
```

**AST 节点结构（以 IfStatement 为例）：**
```python
{
    'type': 'IfStatement',
    'condition': <Expression>,      # 条件表达式
    'then_block': <BlockStatement>, # then 分支
    'else_block': <BlockStatement>  # else 分支（可选）
}
```

**HPLFunction 结构：**
```python
{
    'params': ['a', 'b'],           # 参数名列表
    'body': <BlockStatement>        # 函数体 AST
}
```

---

## 附录：文件清单

| 文件 | 行数 | 核心类/函数 | 复杂度 |
|------|------|-------------|--------|
| `lexer.py` | ~280 | Token, HPLLexer | 中等 |
| `parser.py` | ~250 | HPLParser | 中等 |
| `ast_parser.py` | ~450 | HPLASTParser | 高 |
| `evaluator.py` | ~600 | HPLEvaluator | 高 |
| `models.py` | ~180 | 所有数据模型 | 低 |
| `module_base.py` | ~60 | HPLModule | 低 |
| `module_loader.py` | ~400 | load_module, init_stdlib | 高 |
| `interpreter.py` | ~60 | main() | 低 |
| `package_manager.py` | ~250 | CLI命令 | 中等 |


---

> 文档版本: 1.1.0  
> 最后更新: 2026年  
> 更新内容: 添加改进的 include 系统文档（多路径搜索、函数合并）
> 作者: 奇点工作室
