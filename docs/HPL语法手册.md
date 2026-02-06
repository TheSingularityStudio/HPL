# HPL 语法手册

HPL（基于 YAML 格式的面向对象编程语言）是一种使用 YAML 结构来定义面向对象程序的语言。本手册基于示例文件 `example.yaml` 进行说明，介绍 HPL 的基本语法和结构。

## 1. 文件结构

HPL 程序以 YAML 文件的形式编写，主要包含以下顶级键：

- `classes`：定义类及其方法。
- `objects`：实例化对象。
- `main`：主函数，程序的入口点。
- `call`：调用主函数执行程序。

## 2. 类定义（classes）

类使用 YAML 的映射结构定义。类可以继承其他类，支持方法定义。

### 基本类定义

```yaml
classes:
  ClassName:
    methodName: func(parameters){ code; }
```

- `ClassName`：类名。
- `methodName`：方法名。
- `func(parameters){ code; }`：方法定义，参数可选，代码块使用大括号包围。

### 继承

```yaml
classes:
  BaseClass:
    baseMethod: func(){ echo "base"; }

  DerivedClass:
    parent: BaseClass
    derivedMethod: func(){ this.baseMethod(); }
```

- 使用 `parent` 键指定继承关系，支持单个父类或多个父类列表。
- 子类可以调用父类方法，使用 `this.methodName()`。
- 子类可以重写父类方法，并使用 `super.methodName()` 调用父类方法。

## 3. 对象实例化（objects）

对象通过类实例化，使用构造函数语法。

```yaml
objects:
  objectName: ClassName()
```

- `objectName`：对象名。
- `ClassName()`：调用类的构造函数（假设有默认构造函数）。

## 4. 函数定义

函数使用 `func(parameters){ code; }` 语法定义。

- 参数：用逗号分隔，如 `func(param1, param2)`。
- 代码块：用大括号 `{}` 包围，语句以分号 `;` 结束。
- 调用：`object.method(parameters)` 或 `functionName(parameters)`。

## 5. 控制流

HPL 支持基本的控制流结构。

### 条件语句（if-else）

```yaml
if (condition) {
  code;
} else {
  code;
}
```

- 条件：如 `i % 2 == 0`。

### 循环语句（for）

```yaml
for (initialization; condition; increment) {
  code;
}
```

- 示例：`for (i = 0; i < count; i++) { ... }`

## 6. 异常处理（try-catch）

使用 try-catch 块处理异常。

```yaml
try {
  code;
} catch (error) {
  code;
}
```

- `error`：捕获的异常变量。

## 7. 内置函数和操作符

- `echo`：输出字符串。
- `input`：获取用户输入，可选提示信息参数。例如：`name = input("请输入姓名: ");`
- 字符串连接：使用 `+` 操作符，如 `"Hello " + i`。

- 算术操作符：`+`, `-`, `*`, `/`, `%`。
- 比较操作符：`==`, `!=`, `<`, `>`, `<=`, `>=`。

## 8. 主函数和调用

- `main`：定义主函数，包含程序逻辑。
- `call: main();`：执行主函数。

## 示例程序分析

基于 `examples/example.hpl`：

- 定义了 `BasePrinter` 类，有 `print` 方法。
- `MessagePrinter` 继承 `BasePrinter`，重写 `print` 方法并使用 `super.print()` 调用父类方法，添加 `showmessage` 和 `showmessages` 方法。
- 实例化 `printer` 对象。
- 主函数调用对象方法，展示继承、重写、super 调用、循环和条件语句。

## 注意事项

- HPL 基于 YAML，因此缩进至关重要。
- 字符串应使用双引号包围。
- 所有语句以分号结束。
- 变量作用域：方法内局部，全局对象在 `objects` 下定义。

此手册基于当前示例，可能不涵盖所有 HPL 特性。如有扩展，请参考官方文档。
