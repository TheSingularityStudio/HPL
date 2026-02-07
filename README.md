# HPL
一种基于YAML格式的面向对象的编程语言的运行器

## 解释器架构

HPL 解释器采用模块化设计，使用 Python 实现。架构包括以下组件：

- `models.py`: 定义数据模型，如 HPLClass、HPLObject、HPLFunction 等，用于表示类、对象和函数。
- `lexer.py`: 词法分析器，将源代码字符串转换为 Token 列表，支持行号和列号跟踪。
- `parser.py`: 使用 PyYAML 解析 YAML 文件，将其转换为内部表示形式。
- `ast_parser.py`: AST 解析器，将 Token 列表转换为抽象语法树。
- `evaluator.py`: 执行解析后的结构，处理方法调用、控制流和内置函数。
- `interpreter.py`: 主入口点，加载 YAML 文件，初始化组件并运行程序。

### 依赖
- PyYAML: 用于解析 YAML 文件。

### 使用
运行解释器：`python src/interpreter.py <hpl_file>`

例如：`python src/interpreter.py examples/example.hpl`

## 支持的语法特性

### 1. 基本数据类型
- 整数：`42`, `0`, `-10`
- 浮点数：`3.14`, `-0.5`
- 字符串：`"Hello World"`
- 布尔值：`true`, `false`
- 数组：`[1, 2, 3]`

### 2. 变量和赋值
```yaml
x = 10
name = "HPL"
flag = true
```

### 3. 控制流
- **if-else** 条件语句：
```yaml
if (condition) :
  # then block
else :
  # else block
```

- **for** 循环：
```yaml
for (i = 0; i < count; i++) :
  # loop body
```

- **while** 循环：
```yaml
while (condition) :
  # loop body
```

- **break** 和 **continue**：
```yaml
while (true) :
  if (condition) :
    break
  if (other_condition) :
    continue
```

### 4. 逻辑运算符
- `&&`：逻辑与
- `||`：逻辑或
- `!`：逻辑非

### 5. 类和对象
```yaml
classes:
  MyClass:
    parent: BaseClass
    method: (param) => {
        # method body
      }

objects:
  myObj: MyClass()
```

### 6. 异常处理
```yaml
try :
  # try block
catch (error) :
  # catch block
```

### 7. 内置函数
- `echo(message)`: 输出消息
- `len(array_or_string)`: 获取长度
- `int(value)`: 转换为整数
- `str(value)`: 转换为字符串
- `type(value)`: 获取类型
- `abs(number)`: 绝对值
- `max(a, b, ...)`: 最大值
- `min(a, b, ...)`: 最小值

### 8. 数组操作
```yaml
arr = [1, 2, 3]
first = arr[0]  # 数组访问
```

## 错误处理

HPL 解释器提供详细的错误信息，包括：
- 行号和列号信息
- 调用栈跟踪
- 类型检查错误
- 未定义变量检测
- 除零错误保护

## 示例程序

见 `examples/` 目录：
- `example.hpl`: 主示例程序
- `test_new_features.hpl`: 新特性测试（while、逻辑运算符、break/continue）
- `test_for_loop.hpl`: 循环测试
- `test_comment_comprehensive.hpl`: 注释测试
