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
- 子类可以重写父类方法，并使用 `super.methodName()` 调用父类方法。

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
- `echo`：输出字符串，如 `echo "message"` 或 `echo variable`。

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

### 自增操作符
- `++`：后缀自增
  - 示例：`counter++`

## 8. 数据类型

### 整数（Integer）
- 示例：`42`, `0`, `-10`

### 字符串（String）
- 使用双引号包围
- 示例：`"Hello World"`

### 布尔值（Boolean）
- `true` 或 `false`
- 示例：`flag = true`, `if (false) :`

## 9. 返回值

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

## 10. 主函数和调用

- `main`：定义主函数，包含程序逻辑。
- `call: main()`：执行主函数。

## 11. 完整示例程序分析

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

## 12. 类型检查和错误处理

HPL 解释器现在包含类型检查，提供清晰的错误信息：

- **类型错误**：尝试对非数值使用算术操作符时会报错
  - 示例：`"hello" - "world"` → `TypeError: Unsupported operand type for -: 'str' (expected number)`
  
- **未定义变量**：访问未定义的变量时会报错
  - 示例：使用未定义的 `x` → `ValueError: Undefined variable: 'x'`

- **除零错误**：除法或取模运算中除数为0时会报错
  - 示例：`10 / 0` → `ZeroDivisionError: Division by zero`

- **方法未找到**：调用不存在的方法时会报错
  - 示例：`obj.nonexistent()` → `ValueError: Method 'nonexistent' not found in class 'ClassName'`

## 注意事项

- HPL 基于 YAML，因此缩进至关重要（建议使用 2 个空格）。
- 字符串应使用双引号包围。
- 代码块使用大括号 `{}` 包围，内部使用缩进组织。
- 控制流语句（if、for、try-catch）使用冒号 `:` 表示代码块开始。
- 变量作用域：方法内局部，全局对象在 `objects` 下定义。
- 方法调用使用 `this.methodName()` 或 `object.methodName()`。
- 返回值：方法可以返回任意类型的值，使用 `return` 语句。

此手册基于 `example.hpl` 示例，涵盖了 HPL 的核心语法特性。
