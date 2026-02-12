# HPL 语法概览

**HPL（H Programming Language）** 是一种基于 YAML 格式的面向对象编程语言，使用动态类型系统。

---

## 目录

1. [基本结构](#基本结构)
2. [数据类型](#数据类型)
3. [变量与操作符](#变量与操作符)
4. [控制流](#控制流)
5. [函数与类](#函数与类)
6. [模块系统](#模块系统)
7. [异常处理](#异常处理)
8. [内置函数](#内置函数)

---

## 基本结构

HPL 程序以 YAML 文件形式编写，包含以下顶级键：

```yaml
includes:   # 包含其他 HPL 文件
imports:    # 导入标准库模块
classes:    # 定义类
objects:    # 实例化对象
main:       # 主函数（程序入口）
call:       # 调用入口函数
```

### 最小示例

```yaml
main: () => {
    echo "Hello, HPL!"
  }

call: main()
```

---

## 数据类型

| 类型 | 示例 | 说明 |
|------|------|------|
| **整数** | `42`, `-10` | 整数值 |
| **浮点数** | `3.14`, `-0.5`, `1.5e10` | 小数，支持科学计数法 |
| **字符串** | `"Hello"`, `"Line\n"` | 双引号包围，支持转义 |
| **布尔值** | `true`, `false` | 真/假 |
| **数组** | `[1, 2, 3]` | 有序集合，索引从0开始 |
| **字典** | `{"a": 1, "b": 2}` | 键值对，键必须是字符串 |

### 数组操作

```yaml
arr = [10, 20, 30]

# 访问元素
first = arr[0]      # 10

# 修改元素
arr[0] = 100        # [100, 20, 30]

# 数组拼接
newArr = arr + [40] # [100, 20, 30, 40]
```

### 字典操作

```yaml
person = {"name": "Alice", "age": 30}

# 访问元素
name = person["name"]  # "Alice"

# 修改/添加元素
person["age"] = 31
person["city"] = "Beijing"
```

---

## 变量与操作符

### 变量赋值

```yaml
x = 10              # 整数
pi = 3.14159        # 浮点数
name = "HPL"        # 字符串
flag = true         # 布尔值
```

### 算术操作符

| 操作符 | 说明 | 示例 |
|--------|------|------|
| `+` | 加法/字符串拼接/数组拼接 | `10 + 20`, `"a" + "b"`, `[1] + [2]` |
| `-` | 减法 | `20 - 10` |
| `*` | 乘法 | `5 * 6` |
| `/` | 除法 | `10 / 3` |
| `%` | 取模 | `10 % 3` |
| `++` | 后缀自增 | `i++` |
| `-x` | 一元负号 | `-5` |

### 比较操作符

| 操作符 | 说明 |
|--------|------|
| `==` | 等于 |
| `!=` | 不等于 |
| `<` | 小于 |
| `>` | 大于 |
| `<=` | 小于等于 |
| `>=` | 大于等于 |

### 逻辑操作符

| 操作符 | 说明 | 示例 |
|--------|------|------|
| `!` | 逻辑非 | `!flag` |
| `&&` | 逻辑与 | `a && b` |
| `\|\|` | 逻辑或 | `a \|\| b` |

---

## 控制流

### 条件语句 (if-else)

```yaml
if (condition) :
  # 条件为真时执行
  code
else :
  # 条件为假时执行
  code
```

**示例：**
```yaml
score = 85
if (score >= 90) :
  grade = "A"
else :
  if (score >= 80) :
    grade = "B"
  else :
    grade = "C"
```

### 循环语句 (for in)

```yaml
for (variable in iterable) :
  code
```

**遍历范围：**
```yaml
for (i in range(5)) :
  echo i    # 输出 0, 1, 2, 3, 4
```

**遍历数组：**
```yaml
arr = [10, 20, 30]
for (item in arr) :
  echo item
```

**遍历字典（键）：**
```yaml
person = {"name": "Alice", "age": 30}
for (key in person) :
  echo key    # 输出 "name", "age"
```

**遍历字符串：**
```yaml
text = "Hello"
for (char in text) :
  echo char   # 输出 H, e, l, l, o
```

### While 循环

```yaml
while (condition) :
  code
```

**示例：**
```yaml
i = 0
while (i < 5) :
  echo i
  i++
```

### Break 和 Continue

```yaml
# break - 立即退出循环
for (i in range(10)) :
  if (i == 5) :
    break
  echo i

# continue - 跳过当前迭代
for (i in range(5)) :
  if (i == 2) :
    continue
  echo i
```

---

## 函数与类

### 顶层函数

```yaml
functionName: (param1, param2) => {
    # 函数体
    return result
  }
```

**示例：**
```yaml
add: (a, b) => {
    return a + b
  }

greet: (name) => {
    echo "Hello, " + name + "!"
  }

# 调用任意函数
call: add(5, 3)
```

### 类定义

```yaml
classes:
  ClassName:
    # 构造函数（init 或 __init__）
    init: (param) => {
        this.property = param
      }
    
    # 方法定义
    methodName: () => {
        code
      }
    
    methodWithParams: (a, b) => {
        return a + b
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
    init: () => {
        this.parent.init()    # 调用父类构造函数
      }
    derivedMethod: () => {
        this.baseMethod()     # 调用父类方法
      }
```

### 对象实例化

```yaml
objects:
  objectName: ClassName()
  objectWithParams: ClassName(arg1, arg2)
```

### 完整 OOP 示例

```yaml
classes:
  Rectangle:
    init: (width, height) => {
        this.width = width
        this.height = height
      }
    
    getArea: () => {
        return this.width * this.height
      }

objects:
  rect: Rectangle(10, 5)

main: () => {
    area = rect.getArea()
    echo "Area: " + area    # 输出 50
  }

call: main()
```

---

## 模块系统

### 文件包含 (includes)

用于包含其他 HPL 源代码文件：

```yaml
includes:
  - utils.hpl
  - subdir/helpers.hpl
  - ../common.hpl
```

### 模块导入 (imports)

用于导入标准库或第三方模块：

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
```


### 别名导入

```yaml
imports:
  - math: m        # 使用 m 代替 math
  - time: t        # 使用 t 代替 time

main: () => {
    echo m.PI           # 使用别名访问
    echo t.now()
  }
```

### 模块使用示例

```yaml
imports:
  - math
  - io
  - json
  - crypto
  - random
  - string

main: () => {
    # math 模块
    result = math.sqrt(16)
    
    # io 模块
    content = io.read_file("data.txt")
    io.write_file("output.txt", "Hello")
    
    # json 模块
    data = json.parse('{"a": 1}')
    json.write("data.json", data)
    
    # crypto 模块
    hash = crypto.sha256("Hello")
    encoded = crypto.base64_encode("Hello")
    
    # random 模块
    num = random.random_int(1, 100)
    id = random.uuid()
    
    # string 模块
    words = string.split("a,b,c", ",")
    upper = string.to_upper("hello")
  }
```


---

## 异常处理

### Try-Catch

```yaml
try :
  # 可能出错的代码
  code
catch (error) :
  # 错误处理
  code
```

### Throw 语句

```yaml
try :
  if (x == 0) :
    throw "除数不能为零"
  result = 10 / x
catch (error) :
  echo "错误: " + error
```

### 嵌套异常处理

```yaml
try :
  echo "外层 try"
  try :
    throw "内层错误"
  catch (innerError) :
    echo "内层捕获: " + innerError
catch (outerError) :
  echo "外层捕获: " + outerError
```

---

## 内置函数

### 输入输出

| 函数 | 说明 | 示例 |
|------|------|------|
| `echo value` | 输出到控制台 | `echo "Hello"` |
| `input()` | 获取用户输入 | `name = input()` |
| `input(prompt)` | 带提示的输入 | `age = input("Enter age: ")` |

### 类型转换

| 函数 | 说明 | 示例 |
|------|------|------|
| `int(value)` | 转为整数 | `int("123")` → `123` |
| `str(value)` | 转为字符串 | `str(42)` → `"42"` |

### 数组/字符串操作

| 函数 | 说明 | 示例 |
|------|------|------|
| `len(arr_or_str)` | 获取长度 | `len([1,2,3])` → `3` |
| `type(value)` | 获取类型 | `type(42)` → `"int"` |

### 数值函数

| 函数 | 说明 | 示例 |
|------|------|------|
| `abs(x)` | 绝对值 | `abs(-42)` → `42` |
| `max(a, b, ...)` | 最大值 | `max(10, 20, 5)` → `20` |
| `min(a, b, ...)` | 最小值 | `min(10, 20, 5)` → `5` |

---

## 注释

使用 `#` 开头的单行注释：

```yaml
# 这是注释
x = 10  # 行尾注释

classes:
  MyClass:
    method: () => {
        # 方法内的注释
        return 42
      }
```

---

## 完整示例

```yaml
# 文件包含和模块导入
includes:
  - base.hpl

imports:
  - math: m

# 类定义
classes:
  Calculator:
    init: () => {
        this.result = 0
      }
    
    add: (n) => {
        this.result = this.result + n
        return this.result
      }
    
    getResult: () => {
        return this.result
      }

# 对象实例化
objects:
  calc: Calculator()

# 主函数
main: () => {
    try :
      calc.add(10)
      calc.add(20)
      echo "Result: " + calc.getResult()
      
      # 使用 math 模块
      echo "PI: " + m.PI
      echo "sqrt(16): " + m.sqrt(16)
      
    catch (error) :
      echo "Error: " + error
  }

# 程序入口
call: main()
```

---

## 快速参考卡

```
┌─────────────────────────────────────────────────────────┐
│  HPL 语法快速参考                                        │
├─────────────────────────────────────────────────────────┤
│  数据类型: int, float, string, bool, array, dict         │
│  变量: x = 10                                           │
│  数组: arr = [1, 2, 3], arr[0], arr + [4]               │
│  字典: d = {"a": 1}, d["a"], d["b"] = 2                 │
├─────────────────────────────────────────────────────────┤
│  算术: +  -  *  /  %  ++  -x                             │
│  比较: ==  !=  <  >  <=  >=                              │
│  逻辑: !  &&  ||                                         │
├─────────────────────────────────────────────────────────┤
│  条件: if (cond) : ... else : ...                        │
│  循环: for (i in range(n)) : ...                         │
│        for (item in arr) : ...                           │
│        while (cond) : ...                                │
│  控制: break, continue                                   │
├─────────────────────────────────────────────────────────┤
│  函数: func: (p) => { return x }                         │
│  类:   Class: { init: () => { ... } }                    │
│  继承: parent: BaseClass                                │
│  对象: obj: Class()                                     │
├─────────────────────────────────────────────────────────┤
│  包含: includes: [- file.hpl]                           │
│  导入: imports: [- math, - io, - crypto]                │
│  别名: imports: [- math: m]                             │

├─────────────────────────────────────────────────────────┤
│  异常: try : ... catch (e) : ...                       │
│  抛出: throw "message"                                  │
├─────────────────────────────────────────────────────────┤
│  内置: echo, input, len, type, int, str                 │
│        abs, max, min, range                             │
└─────────────────────────────────────────────────────────┘
```

---

> **提示**: HPL 基于 YAML 格式，缩进非常重要（建议使用 2 个空格）！
