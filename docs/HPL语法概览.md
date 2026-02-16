# HPL 语法概览

**HPL（H Programming Language）** 是一种基于 YAML 格式的面向对象编程语言，使用动态类型系统。

---

## 目录

1. [基本结构](#基本结构)
2. [声明式数据定义](#声明式数据定义)
3. [数据类型](#数据类型)
4. [变量与操作符](#变量与操作符)
5. [控制流](#控制流)
6. [函数与类](#函数与类)
7. [模块系统](#模块系统)
8. [异常处理](#异常处理)
9. [内置函数](#内置函数)
10. [标准库概览](#标准库概览)

---

## 基本结构

HPL 程序以 YAML 文件形式编写，包含以下**原生顶级键**：

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

## 声明式数据定义

**HPL 新特性**：除了六个原生顶级键外，**任何其他顶级键都会自动成为可在 HPL 代码中访问的数据对象**。

### 保留键（原生HPL键）
- `includes`, `imports`, `classes`, `objects`, `main`, `call`

### 自定义数据键示例

```yaml
# 游戏配置
config:
  title: "迷雾森林冒险"
  version: "2.0.0"

# 场景定义
scenes:
  forest:
    name: "迷雾森林"
    description: "你站在一片神秘的森林入口..."
    choices:
      - text: "进入洞穴"
        target: "cave"

# 玩家初始状态
player:
  name: "勇者"
  hp: 100
  gold: 0
```

### 在代码中访问

```yaml
main: () => {
    # 使用点号访问（obj.key 等价于 obj["key"]）
    echo "游戏: " + config.title
    echo "版本: " + config.version
    
    # 嵌套访问
    scene = scenes.forest
    echo "场景: " + scene.name
    
    # 修改数据
    player.hp = 80
    player.gold = player.gold + 10
    
    # 遍历数组
    for (choice in scene.choices) :
      echo "选项: " + choice.text
  }
```

### 优势

- **数据与逻辑分离**：配置、场景、物品等数据声明在 YAML 中，逻辑在 `main` 中
- **充分利用 YAML 结构**：支持嵌套字典、数组等复杂数据结构
- **简洁的访问语法**：使用 `config.title` 代替 `config["title"]`
- **动态修改**：可以在运行时修改数据对象的属性

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

**字典属性访问（新特性）**：
```yaml
config = {"title": "游戏", "version": "1.0"}
echo config.title      # 等价于 config["title"]
config.version = "2.0" # 等价于 config["version"] = "2.0"
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

### 条件语句 (if-elif-else)

```yaml
if (condition) :
  # 条件为真时执行
  code
elif (condition2) :
  # 第二个条件为真时执行
  code
else :
  # 以上条件都不满足时执行
  code
```

**示例：**
```yaml
score = 85
if (score >= 90) :
  grade = "A"
elif (score >= 80) :
  grade = "B"
elif (score >= 70) :
  grade = "C"
else :
  grade = "D"
```

**花括号语法：**
```yaml
if (x > 0) {
  sign = "正数"
} elif (x < 0) {
  sign = "负数"
} else {
  sign = "零"
}
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
  echo key  # 输出 "name", "age"
```

**遍历声明式数据：**
```yaml
scenes:
  forest: {name: "森林", description: "..."}
  cave: {name: "洞穴", description: "..."}

main: () => {
    for (scene_id in scenes) :
      scene = scenes[scene_id]
      echo scene.name
  }
```

### while 循环

```yaml
while (condition) :
  code
```

**示例：**
```yaml
i = 0
while (i < 5) :
  echo "i = " + i
  i++
```

### break 和 continue

```yaml
for (i in range(10)) :
  if (i == 3) :
    continue  # 跳过 3
  if (i == 7) :
    break     # 在 7 时退出
  echo i
```

---

## 函数与类

### 函数定义

```yaml
functionName: (param1, param2) => {
    # 函数体
    return result
  }
```

### 类定义

```yaml
classes:
  ClassName:
    methodName: (param) => {
        return param * 2
      }
```

### 继承

```yaml
classes:
  BaseClass:
    baseMethod: () => {
        echo "Base"
      }

  DerivedClass:
    parent: BaseClass
    derivedMethod: () => {
        this.baseMethod()
      }
```

### 构造函数

```yaml
classes:
  Person:
    init: (name, age) => {
        this.name = name
        this.age = age
      }
```

### 对象实例化

```yaml
objects:
  myObj: ClassName()
  person: Person("Alice", 30)
```

---

## 模块系统

### 包含其他 HPL 文件

```yaml
includes:
  - utils.hpl
  - lib/helpers.hpl
```

### 导入标准库模块

```yaml
imports:
  - math
  - io
  - json
```

**使用示例：**
```yaml
imports:
  - math
  - io
  - json

main: () => {
    # math 模块
    result = math.sqrt(16)
    
    # io 模块
    content = io.read_file("data.txt")
    
    # json 模块
    data = json.parse('{"a": 1}')
  }
```

---

## 异常处理

### try-catch

```yaml
try :
  # 可能抛出异常的代码
  result = 10 / 0
catch (error) :
  echo "错误: " + error
```

### 多 catch 子句

```yaml
try :
  arr = [1, 2, 3]
  val = arr["invalid"]
catch (HPLTypeError type_err) :
  echo "类型错误"
catch (other_err) :
  echo "其他错误"
```

### finally 块

```yaml
try :
  resource = "opened"
  # 使用资源
catch (err) :
  echo "错误"
finally :
  resource = "closed"
  echo "清理完成"
```

### throw 语句

```yaml
try :
  if (x < 0) :
    throw "不能为负数"
  result = math.sqrt(x)
catch (e) :
  echo "错误: " + e
```

---

## 内置函数

| 函数 | 说明 | 示例 |
|------|------|------|
| `echo value` | 输出到控制台 | `echo "Hello"` |
| `len(arr/str)` | 获取长度 | `len([1,2,3])` → `3` |
| `int(value)` | 转为整数 | `int("123")` → `123` |
| `str(value)` | 转为字符串 | `str(42)` → `"42"` |
| `type(value)` | 获取类型 | `type(42)` → `"int"` |
| `abs(number)` | 绝对值 | `abs(-5)` → `5` |
| `max(a, b, ...)` | 最大值 | `max(1, 5, 3)` → `5` |
| `min(a, b, ...)` | 最小值 | `min(1, 5, 3)` → `1` |
| `range(n)` | 生成序列 | `range(3)` → `[0, 1, 2]` |
| `input(prompt?)` | 用户输入 | `name = input("名字: ")` |

---

## 标准库概览

| 模块 | 功能 |
|------|------|
| `math` | 数学函数（sqrt, sin, cos, PI等） |
| `io` | 文件操作（read_file, write_file等） |
| `json` | JSON解析（parse, stringify等） |
| `os` | 系统接口（get_cwd, get_platform等） |
| `time` | 时间处理（now, format, sleep等） |
| `crypto` | 加密哈希（md5, sha256, base64等） |
| `random` | 随机数（random_int, uuid等） |
| `string` | 字符串处理（split, trim, replace等） |
| `re` | 正则表达式（match, find_all, replace等） |
| `net` | 网络请求（get, post, parse_url等） |

**使用示例：**
```yaml
imports:
  - math
  - io
  - json

main: () => {
    echo "PI = " + math.PI
    content = io.read_file("test.txt")
    data = json.parse('{"key": "value"}')
  }
```

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

## 快速参考卡

```
┌─────────────────────────────────────────────────────────┐
│  HPL 语法快速参考                                        │
├─────────────────────────────────────────────────────────┤
│  数据类型: int, float, string, bool, array, dict         │
│  变量: x = 10                                           │
│  数组: arr = [1, 2, 3], arr[0], arr + [4]               │
│  字典: d = {"a": 1}, d["a"], d["b"] = 2                 │
│  字典属性: config.title, player.hp = 100                │
├─────────────────────────────────────────────────────────┤
│  算术: +  -  *  /  %  ++  -x                             │
│  比较: ==  !=  <  >  <=  >=                              │
│  逻辑: !  &&  ||                                         │
├─────────────────────────────────────────────────────────┤
│  条件: if (cond) : ... elif (cond2) : ... else : ...     │
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
│  声明式数据: config, scenes, items, player 等           │
│  任意顶级键自动成为可访问的数据对象                      │
├─────────────────────────────────────────────────────────┤
│  内置: echo, input, len, type, int, str                 │
│        abs, max, min, range                             │
└─────────────────────────────────────────────────────────┘
```

---

> **提示**: HPL 基于 YAML 格式，缩进非常重要（建议使用 2 个空格）！
> 
> **新特性**: 利用声明式数据定义，将配置、场景、物品等数据与逻辑分离，代码更简洁！
