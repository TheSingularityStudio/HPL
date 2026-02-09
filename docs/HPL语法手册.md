# HPL 语法手册

HPL（H Programming Language）是一种基于 YAML 格式的面向对象编程语言，**使用动态类型**。本手册基于示例文件 `example.hpl` 进行说明，介绍 HPL 的基本语法和结构。


## 1. 文件结构

HPL 程序以 YAML 文件的形式编写，主要包含以下顶级键：

- `includes`：包含其他 HPL 文件（代码复用）。
- `imports`：导入标准库或第三方模块（功能扩展）。
- `classes`：定义类及其方法。
- `objects`：实例化对象。
- `main`：主函数，程序的入口点。
- `call`：调用主函数执行程序。

**注意**：`includes` 和 `imports` 用途不同：
- `includes` 用于包含其他 HPL 源代码文件
- `imports` 用于导入标准库模块（如 math、io、json 等）


## 2. 文件包含（includes）

使用 `includes` 关键字可以包含其他 HPL 文件，实现代码复用。

```yaml
includes:
  - base.hpl
  - subdir/utils.hpl
  - ../common.hpl
```

- 使用 YAML 列表格式，每个文件路径前加 `-`。
- 被包含的文件中的类、对象和函数可以在当前文件中使用。
- 被包含的文件会在预处理阶段合并到当前文件中。

### 2.1 路径解析规则

HPL 的 include 系统支持多种路径格式，按以下顺序搜索：

1. **绝对路径**（Unix: `/path/to/file.hpl`, Windows: `C:\path\to\file.hpl`）
2. **相对当前文件目录**（如 `subdir/utils.hpl`）
3. **相对当前工作目录**（程序运行时的目录）
4. **HPL_MODULE_PATHS 中的路径**（标准库和用户库目录）

### 2.2 路径示例

```yaml
# 同级目录
includes:
  - utils.hpl

# 子目录
includes:
  - lib/helpers.hpl
  - modules/math/utils.hpl

# 父目录
includes:
  - ../common.hpl
  - ../../shared/base.hpl

# 绝对路径（不推荐，降低可移植性）
includes:
  - /home/user/hpl_libs/utils.hpl
  - C:\HPL\Libs\utils.hpl
```

### 2.3 函数复用

被包含文件中的函数定义会自动合并到当前文件，可以直接调用：

**utils.hpl**:
```yaml
greet: (name) => {
    echo "Hello, " + name + "!"
  }

calculate: (a, b) => {
    return a + b
  }
```

**main.hpl**:
```yaml
includes:
  - utils.hpl

main: () => {
    greet("World")           # 调用 include 的函数
    result = calculate(5, 3)  # result = 8
    echo "Result: " + result
  }

call: main()
```

### 2.4 错误处理

当 include 文件不存在时，HPL 会显示警告信息：

```
Warning: Include file 'missing.hpl' not found in any search path
Warning: Failed to include 'broken.hpl': [错误详情]
```


## 3. 模块导入（imports）


使用 `imports` 关键字可以导入标准库模块或第三方 Python 模块，扩展语言功能。

```yaml
imports:
  - math
  - io
  - json
  - my_python_module
```

- 使用 YAML 列表格式，每个模块名前加 `-`。
- 导入后通过 `module.function()` 调用模块函数。
- 支持使用别名，使用 YAML 字典格式 `module: alias`（注意：不是 `module as alias` 格式）。

### 别名导入示例

```yaml
imports:
  - math: m              # 使用别名 m 代替 math
  - my_python_module: mp # 使用别名 mp 代替 my_python_module

main: () => {
    # 通过别名访问模块
    echo "PI = " + m.PI
    result = m.sqrt(16)
    echo "sqrt(16) = " + result
    
    greeting = mp.greet("User")
    echo "Greeting: " + greeting
  }
```

## 4. 类定义（classes）


类使用 YAML 的映射结构定义。类可以继承其他类，支持方法定义。

### 基本类定义

```yaml
classes:
  ClassName:
    methodName: () => {
        code
      }
```

- `ClassName`：类名。
- `methodName`：方法名。
- `() => { code }`：方法定义，使用箭头函数语法。
- 参数：在括号内定义，如 `(param1, param2)`。
- 代码块：用大括号 `{}` 包围，使用缩进组织代码。

### 带参数的方法

```yaml
classes:
  ClassName:
    methodName: (param1, param2) => {
        code
      }
```

### 继承

```yaml
classes:
  BaseClass:
    baseMethod: () => {
        code
      }

  DerivedClass:
    parent: BaseClass
    derivedMethod: () => {
        this.baseMethod()
      }
```

- 使用 `parent: BaseClass` 指定继承关系。
- 子类可以调用父类方法，使用 `this.methodName()`。

## 5. 对象实例化（objects）


对象通过类实例化，使用构造函数语法。

```yaml
objects:
  objectName: ClassName()
```

- `objectName`：对象名。
- `ClassName()`：调用类的构造函数（假设有默认构造函数）。

## 6. 控制流


HPL 支持基本的控制流结构，使用冒号和缩进表示代码块。

### 条件语句（if-else）

```yaml
if (condition) :
  code
else :
  code
```

- 条件：如 `i % 2 == 0`。
- 使用冒号 `:` 表示代码块开始，后续代码缩进。

### 循环语句（for）

```yaml
for (initialization; condition; increment) :
  code
```

- 示例：`for (i = 0; i < count; i++) :`
- 循环体使用缩进表示。

### while 循环

```yaml
while (condition) :
  code
```

- 当条件为 `true` 时重复执行循环体
- 示例：
```yaml
i = 0
while (i < 5) :
  echo "i = " + i
  i++
```

### break 和 continue

用于控制循环执行流程：

- `break`：立即退出当前循环
- `continue`：跳过当前迭代，继续下一次循环

```yaml
# break 示例
i = 0
while (true) :
  if (i >= 5) :
    break
  echo i
  i++

# continue 示例
for (i = 0; i < 5; i++) :
  if (i == 2) :
    continue  # 跳过 i == 2 的情况
  echo "i = " + i
```


## 7. 异常处理（try-catch）


使用 try-catch 块处理异常。

```yaml
try :
  code
catch (error) :
  code
```

- `error`：捕获的异常变量。
- 使用冒号和缩进表示代码块。

## 8. 内置函数和操作符


### 内置函数

- `echo value`：输出值到控制台
  - 示例：`echo "Hello"` 或 `echo variable`
  - 注意：括号是可选的

- `len(array_or_string)`：获取数组长度或字符串长度

  - 示例：`len([1, 2, 3])` → `3`，`len("hello")` → `5`

- `int(value)`：将值转换为整数
  - 示例：`int("123")` → `123`，`int(3.14)` → `3`

- `str(value)`：将值转换为字符串
  - 示例：`str(42)` → `"42"`

- `type(value)`：获取值的类型名称
  - 返回类型：`"int"`, `"float"`, `"string"`, `"boolean"`, `"array"` 或类名
  - 示例：`type(42)` → `"int"`，`type([1,2,3])` → `"array"`

- `abs(number)`：获取数值的绝对值
  - 示例：`abs(-42)` → `42`，`abs(-3.14)` → `3.14`

- `max(a, b, ...)`：获取多个值中的最大值
  - 示例：`max(10, 20, 5)` → `20`

- `min(a, b, ...)`：获取多个值中的最小值
  - 示例：`min(10, 20, 5)` → `5`

- `input()` 或 `input(prompt)`：获取用户输入
  - 无参数形式：直接等待用户输入，返回输入的字符串
  - 带参数形式：先显示提示信息，然后等待用户输入，返回输入的字符串
  - 示例：`name = input("请输入名字: ")`，`age = input()`


### 算术操作符

- `+`：加法（支持数值加法和字符串拼接）
  - 如果两边都是数字，执行数值加法：`10 + 20` → `30`
  - 否则执行字符串拼接：`"Hello" + "World"` → `"HelloWorld"`
- `-`：减法（仅支持数值）
- `*`：乘法（仅支持数值）
- `/`：除法（仅支持数值）
- `%`：取模（仅支持数值）

### 比较操作符
- `==`：等于
- `!=`：不等于
- `<`：小于
- `>`：大于
- `<=`：小于等于
- `>=`：大于等于

### 逻辑操作符
- `!`：逻辑非（仅支持布尔值）
  - 示例：`if (!flag) :`

- `&&`：逻辑与（两个条件都为真时结果为真）
  - 示例：`if (a && b) :`

- `||`：逻辑或（至少一个条件为真时结果为真）
  - 示例：`if (a || b) :`

### 自增操作符
- `++`：后缀自增（先返回原值，再增加1）
  - 示例：`counter++`

### 一元操作符
- `-`：一元负号（取相反数）
  - 示例：`-x`，`-(a + b)`
  - 内部实现：将 `-x` 转换为 `0 - x`



## 9. 注释


HPL 支持使用 `#` 开头的单行注释。

```yaml
# 这是注释
x = 10  # 行尾注释

classes:
  # 类前的注释
  MyClass:
    method: () => {
        # 方法内的注释
        a = 10
        return a
      }
```

- 注释从 `#` 开始，到行尾结束
- 注释可以出现在代码的任何位置
- 注释内容会被解释器忽略

## 10. 数据类型


### 整数（Integer）

- 示例：`42`, `0`, `-10`

### 浮点数（Float）
- 支持小数表示
- 示例：`3.14`, `-0.5`, `2.0`

### 字符串（String）
- 使用双引号包围
- 示例：`"Hello World"`
- 支持转义序列：
  - `\n`：换行符
  - `\t`：制表符
  - `\\`：反斜杠
  - `\"`：双引号


### 布尔值（Boolean）
- `true` 或 `false`
- 示例：`flag = true`, `if (false) :`

### 数组（Array）
- 使用方括号 `[]` 定义数组字面量
- 支持存储任意类型的元素
- 使用 `arr[index]` 语法访问数组元素，索引从0开始
- 支持数组元素赋值：`arr[index] = value`

```yaml
# 数组定义
arr = [1, 2, 3, 4, 5]

# 数组访问
first = arr[0]  # 获取第一个元素
second = arr[1]  # 获取第二个元素

# 数组元素赋值
arr[0] = 100  # 修改第一个元素
```

- 数组可以包含不同类型的元素：
```yaml
mixed = [1, "hello", true, 3.14]
```



## 11. 返回值



方法可以使用 `return` 语句返回值。

```yaml
classes:
  Calculator:
    add: (a, b) => {
        return a + b
      }
```

调用方法并获取返回值：

```yaml
main: () => {
    calc = Calculator()
    result = calc.add(10, 20)
    echo "Result: " + result
  }
```

## 12. 主函数和调用


### 基本用法

- `main`：定义主函数，包含程序逻辑。
- `call: main()`：执行主函数。

### 调用任意函数（新特性）

HPL 现在支持调用任意顶层函数，不仅限于 `main`。

```yaml
# 定义多个顶层函数
add: (a, b) => {
    result = a + b
    echo "Adding " + a + " + " + b + " = " + result
    return result
  }

greet: (name) => {
    echo "Hello, " + name + "!"
  }

# 调用任意函数
call: add(5, 3)        # 输出: Adding 5 + 3 = 8
call: greet("World")   # 输出: Hello, World!
```

**特性说明：**
- 可以定义任意数量的顶层函数
- `call` 可以指定要调用的函数名和参数
- 支持带参数的函数调用，如 `call: funcName(arg1, arg2)`
- 如果未指定 `call`，默认执行 `main` 函数（如果存在）


## 13. 完整示例程序分析



基于 `example.hpl`：

```yaml
includes:
  - base.hpl

classes:
  MessagePrinter:
    parent: BasePrinter
    showmessage: () => {
        this.print("Hello World")
      }
    showmessages: (count) => {
        for (i = 0; i < count; i++) :
          if (i % 2 == 0) :
            this.print("Even: Hello World " + i)
          else :
            this.print("Odd: Hello World " + i)
      }

objects:
  printer: MessagePrinter()

main: () => {
    try :
      printer.showmessage()
      printer.showmessages(5)
    catch (error) :
      echo "Error: " + error
  }

call: main()
```

### 示例分析：

1. **文件包含**：通过 `includes` 导入 `base.hpl`，使用其中的 `BasePrinter` 类。
2. **类继承**：`MessagePrinter` 继承 `BasePrinter`，使用 `parent: BasePrinter` 语法。
3. **方法定义**：
   - `showmessage`：无参数方法，调用父类的 `print` 方法。
   - `showmessages`：带参数方法，使用 `for` 循环和 `if-else` 条件语句。
4. **控制流**：
   - `for` 循环遍历 `count` 次。
   - `if-else` 根据奇偶性输出不同消息。
   - 使用 `this.print()` 调用父类方法。
5. **异常处理**：`try-catch` 块捕获并处理可能的错误。
6. **对象实例化**：`printer: MessagePrinter()` 创建对象。
7. **程序执行**：`main` 函数中调用对象方法，`call: main()` 启动程序。

## 14. 新特性综合示例


以下示例展示了 HPL 的新特性，包括 while 循环、逻辑运算符、break/continue、数组和内置函数：

```yaml
classes:
  FeatureDemo:
    # 演示 while 循环和 break/continue
    demo_loop: () => {
        echo "=== While Loop Demo ==="
        i = 0
        sum = 0
        while (i < 10) :
          i++
          if (i == 3) :
            continue  # 跳过 3
          if (i == 7) :
            break     # 在 7 时退出
          sum = sum + i
        echo "Sum (1+2+4+5+6): " + sum
      }
    
    # 演示逻辑运算符
    demo_logic: () => {
        echo ""
        echo "=== Logical Operators Demo ==="
        a = true
        b = false
        
        # && 运算符
        if (a && !b) :
          echo "a && !b is true"
        
        # || 运算符
        if (b || a) :
          echo "b || a is true"
      }
    
    # 演示数组和内置函数
    demo_array: () => {
        echo ""
        echo "=== Array and Built-in Functions Demo ==="
        
        # 数组定义
        numbers = [10, 20, 30, 40, 50]
        echo "Array: " + numbers
        echo "Length: " + len(numbers)
        
        # 数组访问
        first = numbers[0]
        echo "First element: " + first
        
        # 类型检查
        echo "Type of numbers: " + type(numbers)
        echo "Type of first: " + type(first)
        
        # 数值计算
        max_val = max(100, 50, 200, 25)
        min_val = min(100, 50, 200, 25)
        echo "Max: " + max_val
        echo "Min: " + min_val
        
        # 绝对值
        neg = -42
        echo "Absolute of -42: " + abs(neg)
        
        # 类型转换
        num_str = "123"
        converted = int(num_str)
        echo "Converted int: " + converted
      }

objects:
  demo: FeatureDemo()

main: () => {
    demo.demo_loop()
    demo.demo_logic()
    demo.demo_array()
    
    echo ""
    echo "All feature demos completed!"
  }

call: main()
```

### 新特性说明：

1. **while 循环**：`while (i < 10)` 当条件满足时重复执行
2. **break**：立即退出当前循环
3. **continue**：跳过当前迭代，继续下一次循环
4. **逻辑运算符**：`&&`（与）、`||`（或）、`!`（非）
5. **数组**：使用 `[]` 定义，`arr[index]` 访问元素
6. **内置函数**：
   - `len()`：获取数组或字符串长度
   - `type()`：获取值类型
   - `max()`/`min()`：获取最大/最小值
   - `abs()`：获取绝对值
   - `int()`/`str()`：类型转换


## 15. 类型检查和错误处理




HPL 解释器现在包含类型检查，提供清晰的错误信息：

- **类型错误**：尝试对非数值使用算术操作符时会报错
  - 示例：`"hello" - "world"` → `TypeError: Unsupported operand type for -: 'str' (expected number)`
  
- **未定义变量**：访问未定义的变量时会报错
  - 示例：使用未定义的 `x` → `ValueError: Undefined variable: 'x'`

- **除零错误**：除法或取模运算中除数为0时会报错
  - 示例：`10 / 0` → `ZeroDivisionError: Division by zero`

- **方法未找到**：调用不存在的方法时会报错
  - 示例：`obj.nonexistent()` → `ValueError: Method 'nonexistent' not found in class 'ClassName'`

## 16. 注意事项


- HPL 基于 YAML，因此缩进至关重要（建议使用 2 个空格）。
- 缩进规则：
  - 支持空格和制表符（制表符算作 4 个空格）
  - 同一层级的代码必须使用相同的缩进量
  - 控制流语句后的代码块必须缩进
- 字符串应使用双引号包围，支持转义序列（`\n`, `\t`, `\\`, `\"`）。
- 代码块使用大括号 `{}` 包围，内部使用缩进组织。
- 控制流语句（if、for、while、try-catch）使用冒号 `:` 表示代码块开始。
- 变量作用域：方法内局部，全局对象在 `objects` 下定义。
- 方法调用使用 `this.methodName()` 或 `object.methodName()`。
- 返回值：方法可以返回任意类型的值，使用 `return` 语句。
- 注释使用 `#` 开头，可以出现在代码的任何位置。
- 数组索引从 0 开始，访问越界会报错。
- 逻辑运算符 `&&` 和 `||` 具有短路求值特性。
- 后缀自增 `i++` 先返回原值，再增加 1。
- 一元负号 `-x` 将 x 取相反数。
- 模块导入后，使用 `module.function()` 调用模块函数，使用 `module.CONSTANT` 访问模块常量。



## 17. 标准库参考 (Standard Library Reference)

关于模块导入的详细语法（包括基本语法、别名导入、错误格式等），请参考 [3. 模块导入（imports）](#3-模块导入imports)。

### 17.0 可用标准库模块列表

| 模块名 | 描述 |
|--------|------|
| `math` | 数学函数和常量 |
| `io` | 文件输入输出操作 |
| `json` | JSON 解析和生成 |
| `os` | 操作系统接口 |
| `time` | 日期时间处理 |


### 17.1 math 模块 - 数学函数

#### 常量

| 常量 | 值 | 说明 |
|------|-----|------|
| `math.PI` | 3.14159... | 圆周率 |
| `math.E` | 2.71828... | 自然常数 e |
| `math.TAU` | 6.28318... | 2*PI |
| `math.INF` | ∞ | 正无穷大 |
| `math.NAN` | NaN | 非数字 |

#### 函数

**基本运算**
- `math.sqrt(x)` - 平方根
- `math.pow(base, exp)` - 幂运算
- `math.abs(x)` - 绝对值（也可作为内置函数使用）
- `math.max(a, b, ...)` - 最大值（也可作为内置函数使用）
- `math.min(a, b, ...)` - 最小值（也可作为内置函数使用）

**三角函数**
- `math.sin(x)` - 正弦（弧度）
- `math.cos(x)` - 余弦（弧度）
- `math.tan(x)` - 正切（弧度）
- `math.asin(x)` - 反正弦
- `math.acos(x)` - 反余弦
- `math.atan(x)` - 反正切
- `math.atan2(y, x)` - 带象限的反正切

**对数和指数**
- `math.log(x, base)` - 对数（base 可选，默认自然对数）
- `math.log10(x)` - 常用对数（以10为底）
- `math.exp(x)` - e^x

**数值处理**
- `math.floor(x)` - 向下取整
- `math.ceil(x)` - 向上取整
- `math.round(x, ndigits)` - 四舍五入（ndigits 可选）
- `math.trunc(x)` - 截断小数部分
- `math.factorial(n)` - 阶乘
- `math.gcd(a, b)` - 最大公约数

**角度转换**
- `math.degrees(x)` - 弧度转角度
- `math.radians(x)` - 角度转弧度

**特殊函数**
- `math.is_nan(x)` - 检查是否为 NaN
- `math.is_inf(x)` - 检查是否为无穷大


### 17.2 io 模块 - 文件操作

**文件读写**
- `io.read_file(path)` - 读取文件内容为字符串
- `io.write_file(path, content)` - 写入字符串到文件
- `io.append_file(path, content)` - 追加字符串到文件

**文件信息**
- `io.file_exists(path)` - 检查文件是否存在
- `io.get_file_size(path)` - 获取文件大小（字节）
- `io.is_file(path)` - 检查路径是否为文件
- `io.is_dir(path)` - 检查路径是否为目录

**文件操作**
- `io.delete_file(path)` - 删除文件

**目录操作**
- `io.create_dir(path)` - 创建目录
- `io.list_dir(path)` - 列出目录内容（返回数组）


### 17.3 json 模块 - JSON 处理

- `json.parse(json_str)` - 解析 JSON 字符串为 HPL 值
- `json.stringify(value, indent)` - 将 HPL 值转为 JSON 字符串（indent 可选）
- `json.read(path)` - 从文件读取并解析 JSON
- `json.write(path, value, indent)` - 将值写入 JSON 文件（indent 可选）
- `json.is_valid(json_str)` - 检查字符串是否为有效 JSON

**注意**：HPL 的数组可以直接序列化为 JSON 数组。



### 17.4 os 模块 - 操作系统接口

**环境变量**
- `os.get_env(name, default)` - 获取环境变量（default 可选）
- `os.set_env(name, value)` - 设置环境变量

**目录操作**
- `os.get_cwd()` - 获取当前工作目录
- `os.change_dir(path)` - 改变当前目录

**系统信息**
- `os.get_platform()` - 获取操作系统平台（Windows/Linux/Darwin）
- `os.get_python_version()` - 获取 Python 版本
- `os.get_hpl_version()` - 获取 HPL 版本
- `os.cpu_count()` - 获取 CPU 核心数

**路径操作**
- `os.get_path_sep()` - 获取路径分隔符
- `os.get_line_sep()` - 获取行分隔符
- `os.path_join(path1, path2, ...)` - 连接路径
- `os.path_abs(path)` - 获取绝对路径
- `os.path_dir(path)` - 获取目录名
- `os.path_base(path)` - 获取文件名
- `os.path_ext(path)` - 获取文件扩展名
- `os.path_norm(path)` - 规范化路径

**命令执行**
- `os.execute(command)` - 执行系统命令，返回 `{returncode, stdout, stderr}`
- `os.get_args()` - 获取命令行参数（返回数组）

**程序控制**
- `os.exit(code)` - 退出程序（code 可选，默认 0）


### 17.5 time 模块 - 日期时间处理

**时间戳**
- `time.now()` - 获取当前时间戳（秒）
- `time.now_ms()` - 获取当前时间戳（毫秒）
- `time.utc_now()` - 获取 UTC 时间戳

**休眠**
- `time.sleep(seconds)` - 休眠指定秒数
- `time.sleep_ms(milliseconds)` - 休眠指定毫秒数

**时间格式化**
- `time.format(timestamp, format)` - 格式化时间（参数可选，默认当前时间，格式 \"%Y-%m-%d %H:%M:%S\"）
- `time.parse(time_str, format)` - 解析时间字符串为时间戳

**时间组件提取**
- `time.get_year(timestamp)` - 获取年份
- `time.get_month(timestamp)` - 获取月份 (1-12)
- `time.get_day(timestamp)` - 获取日期 (1-31)
- `time.get_hour(timestamp)` - 获取小时 (0-23)
- `time.get_minute(timestamp)` - 获取分钟 (0-59)
- `time.get_second(timestamp)` - 获取秒 (0-59)
- `time.get_weekday(timestamp)` - 获取星期几 (0=周一, 6=周日)

**ISO 格式**
- `time.get_iso_date(timestamp)` - 获取 ISO 格式日期
- `time.get_iso_time(timestamp)` - 获取 ISO 格式时间

**时间计算**
- `time.add_days(timestamp, days)` - 添加天数
- `time.diff_days(timestamp1, timestamp2)` - 计算天数差

**时区**
- `time.local_timezone()` - 获取本地时区偏移（小时）


## 18. 标准库使用示例

以下示例展示了如何使用标准库模块：

```yaml
imports:
  - math
  - io
  - json
  - os
  - time

main: () => {
    # === Math 模块 ===
    echo "=== Math Module ==="
    echo "PI = " + math.PI
    echo "sqrt(16) = " + math.sqrt(16)
    echo "pow(2, 10) = " + math.pow(2, 10)
    echo "sin(PI/2) = " + math.sin(math.PI / 2)
    
    # === Time 模块 ===
    echo ""
    echo "=== Time Module ==="
    echo "Current timestamp: " + time.now()
    echo "Current year: " + time.get_year()
    echo "ISO date: " + time.get_iso_date()
    time.sleep(0.1)  # 休眠 0.1 秒
    
    # === OS 模块 ===
    echo ""
    echo "=== OS Module ==="
    echo "Platform: " + os.get_platform()
    echo "Current directory: " + os.get_cwd()
    echo "CPU count: " + os.cpu_count()
    
    # === IO 模块 ===
    echo ""
    echo "=== IO Module ==="
    test_file = "test_output.txt"
    io.write_file(test_file, "Hello from HPL!")
    content = io.read_file(test_file)
    echo "File content: " + content
    echo "File size: " + io.get_file_size(test_file)
    io.delete_file(test_file)
    
    # === JSON 模块 ===
    echo ""
    echo "=== JSON Module ==="
    # HPL 数组可以直接序列化为 JSON
    data = [1, 2, 3, "hello", "world"]
    json_str = json.stringify(data)
    echo("JSON: " + json_str)
  }

call: main()
```




此手册涵盖了 HPL 的所有核心语法特性，包括基础特性、新增强特性和标准库模块系统。
