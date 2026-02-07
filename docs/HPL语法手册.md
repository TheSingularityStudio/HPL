# HPL 语法手册

HPL（H Programming Language）是一种基于 YAML 格式的面向对象编程语言，**使用动态类型**。本手册基于示例文件 `example.hpl` 进行说明，介绍 HPL 的基本语法和结构。


## 1. 文件结构

HPL 程序以 YAML 文件的形式编写，主要包含以下顶级键：

- `includes`：包含其他 HPL 文件。
- `classes`：定义类及其方法。
- `objects`：实例化对象。
- `main`：主函数，程序的入口点。
- `call`：调用主函数执行程序。

## 2. 文件包含（includes）

使用 `includes` 关键字可以导入其他 HPL 文件，实现代码复用。

```yaml
includes:
  - base.hpl
```

- 使用 YAML 列表格式，每个文件路径前加 `-`。
- 被包含的文件中的类和对象可以在当前文件中使用。

## 3. 类定义（classes）

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

## 4. 对象实例化（objects）

对象通过类实例化，使用构造函数语法。

```yaml
objects:
  objectName: ClassName()
```

- `objectName`：对象名。
- `ClassName()`：调用类的构造函数（假设有默认构造函数）。

## 5. 控制流

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


## 6. 异常处理（try-catch）

使用 try-catch 块处理异常。

```yaml
try :
  code
catch (error) :
  code
```

- `error`：捕获的异常变量。
- 使用冒号和缩进表示代码块。

## 7. 内置函数和操作符

### 内置函数

- `echo(value)`：输出值到控制台
  - 示例：`echo "Hello"` 或 `echo variable`

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


## 8. 注释

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

## 9. 数据类型

### 整数（Integer）

- 示例：`42`, `0`, `-10`

### 浮点数（Float）
- 支持小数表示
- 示例：`3.14`, `-0.5`, `2.0`

### 字符串（String）
- 使用双引号包围
- 示例：`"Hello World"`

### 布尔值（Boolean）
- `true` 或 `false`
- 示例：`flag = true`, `if (false) :`

### 数组（Array）
- 使用方括号 `[]` 定义数组字面量
- 支持存储任意类型的元素
- 使用 `arr[index]` 语法访问数组元素，索引从0开始

```yaml
# 数组定义
arr = [1, 2, 3, 4, 5]

# 数组访问
first = arr[0]  # 获取第一个元素
second = arr[1]  # 获取第二个元素
```

- 数组可以包含不同类型的元素：
```yaml
mixed = [1, "hello", true, 3.14]
```


## 10. 返回值


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

## 11. 主函数和调用


- `main`：定义主函数，包含程序逻辑。
- `call: main()`：执行主函数。

## 12. 完整示例程序分析


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

## 13. 新特性综合示例

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


## 14. 类型检查和错误处理



HPL 解释器现在包含类型检查，提供清晰的错误信息：

- **类型错误**：尝试对非数值使用算术操作符时会报错
  - 示例：`"hello" - "world"` → `TypeError: Unsupported operand type for -: 'str' (expected number)`
  
- **未定义变量**：访问未定义的变量时会报错
  - 示例：使用未定义的 `x` → `ValueError: Undefined variable: 'x'`

- **除零错误**：除法或取模运算中除数为0时会报错
  - 示例：`10 / 0` → `ZeroDivisionError: Division by zero`

- **方法未找到**：调用不存在的方法时会报错
  - 示例：`obj.nonexistent()` → `ValueError: Method 'nonexistent' not found in class 'ClassName'`

## 15. 注意事项

- HPL 基于 YAML，因此缩进至关重要（建议使用 2 个空格）。
- 字符串应使用双引号包围。
- 代码块使用大括号 `{}` 包围，内部使用缩进组织。
- 控制流语句（if、for、while、try-catch）使用冒号 `:` 表示代码块开始。
- 变量作用域：方法内局部，全局对象在 `objects` 下定义。
- 方法调用使用 `this.methodName()` 或 `object.methodName()`。
- 返回值：方法可以返回任意类型的值，使用 `return` 语句。
- 注释使用 `#` 开头，可以出现在代码的任何位置。
- 数组索引从 0 开始，访问越界会报错。
- 逻辑运算符 `&&` 和 `||` 具有短路求值特性。
- 后缀自增 `i++` 先返回原值，再增加 1。

此手册涵盖了 HPL 的所有核心语法特性，包括基础特性和新增强特性。
