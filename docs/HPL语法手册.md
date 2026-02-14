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

### 4.1 基本类定义

```yaml
classes:
  ClassName:
    methodName: () => {
        code
      }
```

- `ClassName`：类名。
- `methodName`：方法名。
- `() => { code }`：方法定义，使用**箭头函数语法**。
- 参数：在括号内定义，如 `(param1, param2)`。
- 代码块：用大括号 `{}` 包围，使用缩进组织代码。

**箭头函数语法说明：**
HPL 使用箭头函数 `=>` 定义方法，这是 HPL 的核心语法特性。箭头函数使代码更加简洁，同时保持清晰的结构。


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

### 构造函数

HPL 支持使用 `init` 或 `__init__` 作为构造函数名（推荐使用简化的 `init`）：

```yaml
classes:
  Shape:
    # 使用简化的 init 作为构造函数名
    init: (name) => {
        this.name = name
      }
    
    getName: () => {
        return this.name
      }

  Rectangle:
    parent: Shape
    init: (width, height) => {
        # 调用父类构造函数
        this.parent.init("矩形")
        this.width = width
        this.height = height
      }
```

- 构造函数在对象实例化时自动调用
- 支持 `init` 和 `__init__` 两种形式（`init` 是 `__init__` 的别名）
- 子类可以通过 `this.parent.init(...)` 调用父类构造函数


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

### 循环语句（for in）

HPL 使用 `for in` 语法进行循环迭代，支持遍历范围、数组、字典和字符串。

```yaml
for (variable in iterable) :
  code
```

- **基本语法**：`for (i in range(5)) :`
- **遍历数组**：`for (item in arr) :`
- **遍历字典**：`for (key in dict) :`（遍历字典的键）
- **遍历字符串**：`for (char in str) :`（遍历字符串的每个字符）
- 循环体使用缩进表示。

#### 支持的迭代对象

1. **range 函数**：`range(n)` 生成 0 到 n-1 的整数序列
   ```yaml
   for (i in range(5)) :
     echo i  # 输出 0, 1, 2, 3, 4
   ```

2. **数组**：直接遍历数组元素
   ```yaml
   arr = [10, 20, 30]
   for (item in arr) :
     echo item  # 输出 10, 20, 30
   ```

3. **字典**：遍历字典的键
   ```yaml
   person = {"name": "Alice", "age": 30}
   for (key in person) :
     echo key  # 输出 "name", "age"
   ```

4. **字符串**：遍历每个字符
   ```yaml
   text = "Hello"
   for (char in text) :
     echo char  # 输出 H, e, l, l, o
   ```


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
for (i in range(5)) :
  if (i == 2) :
    continue  # 跳过 i == 2 的情况
  echo "i = " + i

```


## 7. 异常处理（try-catch-finally 和 throw）


使用 try-catch-finally 块处理异常，使用 throw 语句抛出异常。

### try-catch 基本用法

```yaml
try :
  code
catch (error) :
  code
```

- `error`：捕获的异常变量。
- 使用冒号和缩进表示代码块。

### 多 catch 子句（异常类型匹配）

HPL 支持多个 catch 子句，可以根据异常类型进行匹配：

```yaml
try :
  # 可能抛出异常的代码
  arr = [1, 2, 3]
  val = arr["invalid"]  # 类型错误
catch (HPLTypeError type_err) :
  echo "类型错误: " + type_err
catch (other_err) :
  echo "其他错误: " + other_err
```

- 多个 catch 子句按顺序匹配，第一个匹配的 catch 会被执行
- 可以在 catch 括号中指定异常类型，如 `HPLTypeError`、`ZeroDivisionError` 等
- 如果不指定类型，将捕获所有类型的异常

### finally 块

finally 块用于执行清理操作，无论是否发生异常都会执行：

```yaml
try :
  resource = "opened"
  # 使用资源
  result = 10 / 0
catch (err) :
  echo "捕获错误: " + err
finally :
  resource = "closed"
  echo "资源已关闭: " + resource
```

- finally 块在 try 和 catch 之后执行
- 无论 try 中是否发生异常、catch 是否捕获，finally 都会执行
- 常用于资源清理（关闭文件、释放锁等）

**注意**：如果在 finally 块中使用 `return`，会覆盖 try 或 catch 中的返回值：

```yaml
test_finally_return: () => {
    try :
      result = "try 返回值"
    catch (err) :
      result = "catch 返回值"
    finally :
      result = "finally 返回值"  # 这会覆盖之前的返回值
    return result  # 返回 "finally 返回值"
  }
```

### throw 语句

使用 `throw` 语句主动抛出异常：

```yaml
try :
  if (x == 0) :
    throw "除数不能为零"
  result = 10 / x
catch (error) :
  echo "错误: " + error
```

- `throw` 后面可以跟任意表达式，表达式的值将被转换为字符串作为错误信息
- 如果没有提供表达式，将抛出默认错误信息 "Exception thrown"
- throw 语句只能在 try-catch 块中使用（或任何会被捕获的地方）

### 嵌套异常处理

```yaml
try :
  echo "外层 try 开始"
  try :
    echo "内层 try"
    throw "内层错误"
  catch (innerError) :
    echo "内层捕获: " + innerError
  echo "外层 try 继续"
catch (outerError) :
  echo "外层捕获: " + outerError
```



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

- `+`：加法（支持数值加法、字符串拼接和**数组拼接**）
  - 如果两边都是数字，执行数值加法：`10 + 20` → `30`
  - 如果两边都是数组，执行数组拼接：`[1, 2] + [3, 4]` → `[1, 2, 3, 4]`
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
- 支持科学计数法：`1.5e10`, `-2.5e-3`
- 整数和浮点数混合运算时，结果自动提升为浮点数


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

### 空值（Null）
- `null`
- 表示空值或未定义值
- 示例：`value = null`, `if (value == null) :`

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

### 字典/映射（Dictionary/Map）

- 使用花括号 `{}` 定义字典字面量
- 键必须是字符串，值可以是任意类型
- 使用 `dict[key]` 语法访问字典元素
- 支持字典元素赋值：`dict[key] = value`

```yaml
# 字典定义
person = {
  "name": "Alice",
  "age": 30,
  "is_student": false
}

# 字典访问
name = person["name"]  # 获取值 "Alice"
age = person["age"]   # 获取值 30

# 字典元素赋值
person["age"] = 31
person["city"] = "Beijing"  # 添加新键值对
```

- 字典可以嵌套：
```yaml
nested = {
  "user": {
    "name": "Bob",
    "contacts": {
      "email": "bob@example.com"
    }
  }
}
email = nested["user"]["contacts"]["email"]
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

## 12. 函数定义和调用


### 基本用法

- `main`：定义主函数，包含程序逻辑。
- `call: main()`：执行主函数。

### 箭头函数语法

HPL 使用箭头函数语法定义函数：

```yaml
functionName: (param1, param2) => {
    # 函数体
    return result
  }
```

- 参数列表放在括号 `()` 中
- 使用 `=>` 箭头符号分隔参数和函数体
- 函数体使用大括号 `{}` 包围，内部使用缩进组织代码

### 顶层函数定义

HPL 支持定义任意数量的顶层函数，不限于 `main`：

```yaml
# 定义多个顶层函数
add: (a, b) => {
    result = a + b
    echo "Adding " + a + " + " + b + " = " + result
    return result
  }

greet: (name) => {
    message = "Hello, " + name + "!"
    echo message
    return message
  }

# 定义主函数（可选）
main: () => {
    echo "This is the main function"
    result = add(10, 20)
    echo "Result from main: " + result
  }
```

### 调用任意函数

`call` 可以调用任意顶层函数，不仅限于 `main`：

```yaml
# 调用 add 函数（而不是 main）
call: add(5, 3)        # 输出: Adding 5 + 3 = 8

# 调用 greet 函数
call: greet("World")   # 输出: Hello, World!
```

**特性说明：**
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
        for (i in range(count)) :
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
    # 演示 for in 循环和 break/continue
    demo_loop: () => {
        echo "=== For In Loop Demo ==="
        sum = 0
        for (i in range(10)) :
          if (i == 3) :
            continue  # 跳过 3
          if (i == 7) :
            break     # 在 7 时退出
          sum = sum + i
        echo "Sum (0+1+2+4+5+6): " + sum
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
- 箭头函数 `=>` 是 HPL 的核心语法，用于定义函数和方法。

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
| `crypto` | 加密哈希和编码功能 |
| `random` | 随机数生成 |
| `string` | 字符串处理 |
| `re` | 正则表达式操作 |
| `net` | HTTP 网络请求 |

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
| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `math.sqrt(x)` | number | float | 平方根 |
| `math.pow(base, exp)` | number, number | float | 幂运算 |
| `math.abs(x)` | number | number | 绝对值（也可作为内置函数使用） |
| `math.max(a, b, ...)` | number... | number | 最大值（也可作为内置函数使用） |
| `math.min(a, b, ...)` | number... | number | 最小值（也可作为内置函数使用） |

**三角函数**
| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `math.sin(x)` | number (弧度) | float | 正弦 |
| `math.cos(x)` | number (弧度) | float | 余弦 |
| `math.tan(x)` | number (弧度) | float | 正切 |
| `math.asin(x)` | number (-1~1) | float (弧度) | 反正弦 |
| `math.acos(x)` | number (-1~1) | float (弧度) | 反余弦 |
| `math.atan(x)` | number | float (弧度) | 反正切 |
| `math.atan2(y, x)` | number, number | float (弧度) | 带象限的反正切，处理 y/x 的符号 |

**对数和指数**
| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `math.log(x, base?)` | number, number? | float | 对数，base 可选，默认自然对数 e |
| `math.log10(x)` | number | float | 常用对数（以10为底） |
| `math.exp(x)` | number | float | e 的 x 次幂 |

**数值处理**
| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `math.floor(x)` | number | int | 向下取整 |
| `math.ceil(x)` | number | int | 向上取整 |
| `math.round(x, ndigits?)` | number, int? | number | 四舍五入，ndigits 指定小数位数 |
| `math.trunc(x)` | number | int | 截断小数部分 |
| `math.factorial(n)` | int (≥0) | int | 阶乘 |
| `math.gcd(a, b)` | int, int | int | 最大公约数 |

**角度转换**
| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `math.degrees(x)` | number (弧度) | float | 弧度转角度 |
| `math.radians(x)` | number (角度) | float | 角度转弧度 |

**特殊函数**
| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `math.is_nan(x)` | number | boolean | 检查是否为 NaN |
| `math.is_inf(x)` | number | boolean | 检查是否为无穷大 |



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


### 17.6 crypto 模块 - 加密哈希和编码

提供加密哈希、编码功能和安全随机数生成。

#### 哈希函数

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `crypto.md5(data)` | string/bytes | string | 计算 MD5 哈希（32位十六进制） |
| `crypto.sha1(data)` | string/bytes | string | 计算 SHA1 哈希（40位十六进制） |
| `crypto.sha256(data)` | string/bytes | string | 计算 SHA256 哈希（64位十六进制） |
| `crypto.sha512(data)` | string/bytes | string | 计算 SHA512 哈希（128位十六进制） |
| `crypto.sha3_256(data)` | string/bytes | string | 计算 SHA3-256 哈希 |
| `crypto.sha3_512(data)` | string/bytes | string | 计算 SHA3-512 哈希 |
| `crypto.blake2b(data, digest_size?)` | string/bytes, int? | string | 计算 BLAKE2b 哈希 |
| `crypto.blake2s(data, digest_size?)` | string/bytes, int? | string | 计算 BLAKE2s 哈希 |
| `crypto.hash(data, algorithm?)` | string/bytes, string? | string | 使用指定算法计算哈希，默认 sha256 |
| `crypto.hmac(data, key, algorithm?)` | string/bytes, string/bytes, string? | string | 计算 HMAC 签名，默认 sha256 |

#### 编码函数

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `crypto.base64_encode(data)` | string/bytes | string | Base64 编码 |
| `crypto.base64_decode(data)` | string | string/bytes | Base64 解码 |
| `crypto.base64_urlsafe_encode(data)` | string/bytes | string | URL 安全 Base64 编码 |
| `crypto.base64_urlsafe_decode(data)` | string | string/bytes | URL 安全 Base64 解码 |
| `crypto.url_encode(data)` | string | string | URL 编码 |
| `crypto.url_decode(data)` | string | string | URL 解码 |
| `crypto.url_encode_plus(data)` | string | string | URL 编码（空格转为+） |
| `crypto.url_decode_plus(data)` | string | string | URL 解码（+转为空格） |

#### 安全随机数生成

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `crypto.secure_random_bytes(length)` | int | bytes | 生成加密安全随机字节 |
| `crypto.secure_random_hex(length)` | int | string | 生成加密安全随机十六进制字符串 |
| `crypto.secure_random_urlsafe(length)` | int | string | 生成 URL 安全随机字符串 |
| `crypto.secure_choice(sequence)` | array/string | any | 从序列中安全随机选择 |
| `crypto.compare_digest(a, b)` | string/bytes, string/bytes | boolean | 安全比较（防时序攻击） |

#### 密钥派生

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `crypto.pbkdf2_hmac(password, salt, iterations?, dklen?, hash_name?)` | string/bytes, string/bytes, int?, int?, string? | string | PBKDF2 密钥派生 |
| `crypto.scrypt(password, salt, n?, r?, p?, dklen?)` | string/bytes, string/bytes, int?, int?, int?, int? | string | scrypt 密钥派生 |


### 17.7 random 模块 - 随机数生成

提供随机数生成和 UUID 生成功能。

#### 基础随机数

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `random.random()` | - | float | 生成 [0, 1) 范围内的随机浮点数 |
| `random.random_int(min, max)` | int, int | int | 生成 [min, max] 范围内的随机整数 |
| `random.random_float(min, max)` | number, number | float | 生成 [min, max) 范围内的随机浮点数 |
| `random.choice(array)` | array | any | 从数组中随机选择一个元素 |
| `random.shuffle(array)` | array | array | 随机打乱数组（原地修改） |
| `random.sample(array, count)` | array, int | array | 无放回抽样指定数量元素 |
| `random.seed(value)` | int/float/string | boolean | 设置随机种子 |
| `random.random_bool()` | - | boolean | 生成随机布尔值 |

#### UUID 生成

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `random.uuid()` | - | string | 生成 UUID v4（随机） |
| `random.uuid1()` | - | string | 生成 UUID v1（基于时间和 MAC） |
| `random.uuid3(namespace, name)` | string, string | string | 生成 UUID v3（基于 MD5） |
| `random.uuid5(namespace, name)` | string, string | string | 生成 UUID v5（基于 SHA1） |

**命名空间常量**：`dns`, `url`, `oid`, `x500`

#### 随机字节

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `random.random_bytes(length)` | int | bytes | 生成指定长度随机字节 |
| `random.random_hex(length)` | int | string | 生成指定长度随机十六进制字符串 |

#### 统计分布随机数

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `random.gauss(mu?, sigma?)` | number?, number? | float | 高斯分布，默认 mu=0, sigma=1 |
| `random.triangular(low?, high?, mode?)` | number?, number?, number? | float | 三角分布，默认 low=0, high=1 |
| `random.expovariate(lambd)` | number | float | 指数分布 |
| `random.betavariate(alpha, beta)` | number, number | float | Beta 分布 |
| `random.gammavariate(alpha, beta)` | number, number | float | Gamma 分布 |
| `random.lognormvariate(mu, sigma)` | number, number | float | 对数正态分布 |
| `random.vonmisesvariate(mu, kappa)` | number, number | float | von Mises 分布 |
| `random.paretovariate(alpha)` | number | float | Pareto 分布 |
| `random.weibullvariate(alpha, beta)` | number, number | float | Weibull 分布 |

#### 状态管理

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `random.getstate()` | - | state | 获取随机数生成器状态 |
| `random.setstate(state)` | state | boolean | 恢复随机数生成器状态 |


### 17.8 string 模块 - 字符串处理

提供字符串处理功能。

#### 基础操作

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `string.length(s)` | string | int | 获取字符串长度 |
| `string.split(s, delimiter?, maxsplit?)` | string, string?, int? | array | 分割字符串为数组 |
| `string.join(array, delimiter?)` | array, string? | string | 使用分隔符连接数组元素 |
| `string.replace(s, old, new, count?)` | string, string, string, int? | string | 替换子串 |
| `string.substring(s, start, end?)` | string, int, int? | string | 截取子字符串 |

#### 空白处理

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `string.trim(s, chars?)` | string, string? | string | 去除首尾空白或指定字符 |
| `string.trim_start(s, chars?)` | string, string? | string | 去除开头空白或指定字符 |
| `string.trim_end(s, chars?)` | string, string? | string | 去除结尾空白或指定字符 |
| `string.is_empty(s)` | string | boolean | 检查字符串是否为空 |
| `string.is_blank(s)` | string | boolean | 检查字符串是否为空或仅空白 |

#### 大小写转换

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `string.to_upper(s)` | string | string | 转为大写 |
| `string.to_lower(s)` | string | string | 转为小写 |
| `string.capitalize(s)` | string | string | 首字母大写 |
| `string.title_case(s)` | string | string | 每个单词首字母大写 |
| `string.swap_case(s)` | string | string | 交换大小写 |

#### 查找和检查

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `string.index_of(s, substr, start?)` | string, string, int? | int | 查找子串位置，未找到返回 -1 |
| `string.last_index_of(s, substr, start?)` | string, string, int? | int | 从后往前查找子串位置 |
| `string.starts_with(s, prefix)` | string, string | boolean | 检查是否以指定前缀开头 |
| `string.ends_with(s, suffix)` | string, string | boolean | 检查是否以指定后缀结尾 |
| `string.contains(s, substr)` | string, string | boolean | 检查是否包含子串 |
| `string.count(s, substr)` | string, string | int | 统计子串出现次数 |

#### 其他操作

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `string.reverse(s)` | string | string | 反转字符串 |
| `string.repeat(s, count)` | string, int | string | 重复字符串指定次数 |
| `string.pad_start(s, length, pad?)` | string, int, string? | string | 在开头填充至指定长度 |
| `string.pad_end(s, length, pad?)` | string, int, string? | string | 在结尾填充至指定长度 |


### 17.9 re 模块 - 正则表达式

提供正则表达式匹配、搜索、替换等功能。

#### 正则表达式标志

| 标志 | 说明 |
|------|------|
| `i` | 忽略大小写 (IGNORECASE) |
| `m` | 多行模式 (MULTILINE) |
| `s` | 点匹配所有字符包括换行 (DOTALL) |
| `x` | 详细模式，允许注释和空白 (VERBOSE) |
| `a` | ASCII 匹配 (ASCII) |
| `u` | Unicode 匹配，默认开启 (UNICODE) |
| `l` | 本地化匹配 (LOCALE) |

**使用方式**：将标志字母组合成字符串传入，如 `"im"` 表示忽略大小写且多行模式。

#### 匹配函数

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `re.match(pattern, string, flags?)` | string, string, string? | object/null | 从字符串开头匹配，返回匹配对象或 null |
| `re.search(pattern, string, flags?)` | string, string, string? | object/null | 在字符串中搜索，返回第一个匹配对象或 null |
| `re.test(pattern, string, flags?)` | string, string, string? | boolean | 测试字符串是否匹配正则表达式 |

**匹配对象结构**：
```yaml
{
  'group': "匹配的完整字符串",
  'groups': ["捕获组1", "捕获组2"],  # 捕获组数组
  'start': 0,  # 匹配开始位置
  'end': 5,    # 匹配结束位置
  'span': [0, 5]  # 起止位置数组
}
```

#### 查找函数

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `re.find_all(pattern, string, flags?)` | string, string, string? | array | 查找所有匹配项，返回匹配字符串数组 |
| `re.find_iter(pattern, string, flags?)` | string, string, string? | array | 查找所有匹配项，返回匹配对象数组 |

#### 修改函数

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `re.replace(pattern, repl, string, count?, flags?)` | string, string, string, int?, string? | string | 替换匹配项，count=0 表示替换所有 |
| `re.split(pattern, string, maxsplit?, flags?)` | string, string, int?, string? | array | 使用正则表达式分割字符串 |
| `re.escape(string)` | string | string | 转义字符串中的正则表达式特殊字符 |

#### 工具函数

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `re.compile(pattern, flags?)` | string, string? | object | 预编译正则表达式，返回模式对象 |
| `re.validate(pattern_name, string)` | string, string | boolean | 使用预定义模式验证字符串 |

**支持的预定义模式**：
- `email` - 邮箱地址
- `url` - URL 地址
- `ip` - IP 地址
- `phone` - 中国大陆手机号
- `id_card` - 中国大陆身份证
- `chinese` - 中文字符
- `english` - 英文字母
- `number` - 数字
- `whitespace` - 空白字符
- `word` - 单词字符

#### 预定义模式常量

| 常量 | 说明 |
|------|------|
| `re.PATTERN_EMAIL` | 邮箱匹配模式 |
| `re.PATTERN_URL` | URL 匹配模式 |
| `re.PATTERN_IP` | IP 地址匹配模式 |
| `re.PATTERN_PHONE` | 手机号匹配模式 |
| `re.PATTERN_ID_CARD` | 身份证匹配模式 |
| `re.PATTERN_CHINESE` | 中文字符匹配模式 |
| `re.PATTERN_ENGLISH` | 英文字母匹配模式 |
| `re.PATTERN_NUMBER` | 数字匹配模式 |
| `re.PATTERN_WHITESPACE` | 空白字符匹配模式 |
| `re.PATTERN_WORD` | 单词字符匹配模式 |


### 17.10 net 模块 - 网络请求

提供 HTTP 客户端功能，支持 GET、POST 等请求。

#### HTTP 请求函数

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `net.get(url, headers?, timeout?, verify_ssl?)` | string, dict?, number?, boolean? | object | 发送 HTTP GET 请求 |
| `net.post(url, data?, headers?, timeout?, verify_ssl?)` | string, any?, dict?, number?, boolean? | object | 发送 HTTP POST 请求，data 可为字符串或字典 |
| `net.put(url, data?, headers?, timeout?, verify_ssl?)` | string, any?, dict?, number?, boolean? | object | 发送 HTTP PUT 请求 |
| `net.delete(url, headers?, timeout?, verify_ssl?)` | string, dict?, number?, boolean? | object | 发送 HTTP DELETE 请求 |
| `net.head(url, headers?, timeout?, verify_ssl?)` | string, dict?, number?, boolean? | object | 发送 HTTP HEAD 请求 |
| `net.request(method, url, data?, headers?, timeout?, verify_ssl?)` | string, string, any?, dict?, number?, boolean? | object | 发送任意 HTTP 请求 |

**响应对象结构**：
```yaml
{
  'status': 200,        # HTTP 状态码
  'reason': "OK",       # 状态描述
  'headers': {},        # 响应头字典
  'body': "响应内容",    # 响应体字符串
  'url': "最终URL"      # 实际请求的 URL（可能经过重定向）
}
```

#### URL 处理函数

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `net.encode_url(params)` | dict | string | 将参数字典编码为 URL 查询字符串 |
| `net.decode_url(query_string)` | string | dict | 解码 URL 查询字符串为字典 |
| `net.parse_url(url)` | string | object | 解析 URL 组件 |
| `net.build_url(base, params?)` | string, dict? | string | 构建完整 URL |

**parse_url 返回结构**：
```yaml
{
  'scheme': "https",     # 协议
  'netloc': "api.example.com",  # 网络位置
  'path': "/users",      # 路径
  'params': "",          # 参数
  'query': "id=123",     # 查询字符串
  'fragment': "",        # 片段
  'username': null,      # 用户名
  'password': null,      # 密码
  'hostname': "api.example.com",  # 主机名
  'port': null           # 端口
}
```

#### HTTP 状态码检查函数

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `net.is_success(status_code)` | int | boolean | 检查是否为 2xx 成功状态码 |
| `net.is_redirect(status_code)` | int | boolean | 检查是否为 3xx 重定向状态码 |
| `net.is_client_error(status_code)` | int | boolean | 检查是否为 4xx 客户端错误状态码 |
| `net.is_server_error(status_code)` | int | boolean | 检查是否为 5xx 服务器错误状态码 |

#### HTTP 状态码常量

| 常量 | 值 | 说明 |
|------|-----|------|
| `net.STATUS_OK` | 200 | 请求成功 |
| `net.STATUS_CREATED` | 201 | 已创建 |
| `net.STATUS_ACCEPTED` | 202 | 已接受 |
| `net.STATUS_NO_CONTENT` | 204 | 无内容 |
| `net.STATUS_MOVED_PERMANENTLY` | 301 | 永久重定向 |
| `net.STATUS_FOUND` | 302 | 临时重定向 |
| `net.STATUS_NOT_MODIFIED` | 304 | 未修改 |
| `net.STATUS_BAD_REQUEST` | 400 | 请求错误 |
| `net.STATUS_UNAUTHORIZED` | 401 | 未授权 |
| `net.STATUS_FORBIDDEN` | 403 | 禁止访问 |
| `net.STATUS_NOT_FOUND` | 404 | 未找到 |
| `net.STATUS_METHOD_NOT_ALLOWED` | 405 | 方法不允许 |
| `net.STATUS_INTERNAL_ERROR` | 500 | 服务器内部错误 |
| `net.STATUS_NOT_IMPLEMENTED` | 501 | 未实现 |
| `net.STATUS_BAD_GATEWAY` | 502 | 网关错误 |
| `net.STATUS_SERVICE_UNAVAILABLE` | 503 | 服务不可用 |


## 18. 标准库使用示例



以下示例展示了如何使用标准库模块：

```yaml
imports:
  - math
  - io
  - json
  - os
  - time
  - crypto
  - random
  - string

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
    # HPL 的数组可以直接序列化为 JSON
    data = [1, 2, 3, "hello", "world"]
    json_str = json.stringify(data)
    echo("JSON: " + json_str)
    
    # === Crypto 模块 ===
    echo ""
    echo "=== Crypto Module ==="
    data = "Hello, HPL!"
    echo "MD5: " + crypto.md5(data)
    echo "SHA256: " + crypto.sha256(data)
    echo "Base64: " + crypto.base64_encode(data)
    echo "URL encoded: " + crypto.url_encode(data)
    echo "Secure random hex: " + crypto.secure_random_hex(16)
    
    # === Random 模块 ===
    echo ""
    echo "=== Random Module ==="
    echo "Random int (1-100): " + random.random_int(1, 100)
    echo "Random float: " + random.random()
    echo "UUID: " + random.uuid()
    arr = [1, 2, 3, 4, 5]
    echo "Random choice: " + random.choice(arr)
    
    # === String 模块 ===
    echo ""
    echo "=== String Module ==="
    text = "  Hello, HPL!  "
    echo "Original: '" + text + "'"
    echo "Trimmed: '" + string.trim(text) + "'"
    echo "Upper: " + string.to_upper(text)
    echo "Lower: " + string.to_lower(text)
    words = string.split("apple,banana,cherry", ",")
    echo "Split: " + words
    echo "Join: " + string.join(words, " - ")
    
    # === Re 模块 ===
    echo ""
    echo "=== Re Module ==="
    # 测试字符串是否匹配
    if (re.test("\\d+", "Hello123")) :
      echo "字符串包含数字"
    
    # 查找所有匹配
    numbers = re.find_all("\\d+", "a1b2c3")
    echo "找到的数字: " + numbers
    
    # 替换匹配项
    result = re.replace("\\d+", "X", "a1b2c3")
    echo "替换后: " + result
    
    # 分割字符串
    parts = re.split("\\s+", "hello   world  test")
    echo "分割结果: " + parts
    
    # 验证邮箱格式
    email = "user@example.com"
    if (re.validate("email", email)) :
      echo "邮箱格式正确: " + email
    
    # 使用预定义模式常量
    echo "邮箱模式: " + re.PATTERN_EMAIL
    
    # === Net 模块 ===
    echo ""
    echo "=== Net Module ==="
    # URL 解析
    url_info = net.parse_url("https://api.example.com/users?id=123")
    echo "协议: " + url_info["scheme"]
    echo "主机: " + url_info["hostname"]
    
    # URL 编码
    params = {"name": "张三", "age": "25"}
    query = net.encode_url(params)
    echo "编码后: " + query
    
    # 构建完整 URL
    full_url = net.build_url("https://api.example.com/search", {"q": "hpl"})
    echo "完整URL: " + full_url
    
    # HTTP 状态码检查
    status = 200
    if (net.is_success(status)) :
      echo "请求成功"
    
    # 使用 HTTP 状态码常量
    echo "OK状态码: " + net.STATUS_OK
    echo "Not Found状态码: " + net.STATUS_NOT_FOUND
  }

call: main()


```


此手册涵盖了 HPL 的所有核心语法特性，包括基础特性、新增强特性和标准库模块系统。
