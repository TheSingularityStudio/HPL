# HPL Runtime

[![PyPI version](https://badge.fury.io/py/hpl-runtime.svg)](https://badge.fury.io/py/hpl-runtime)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

**HPL（H Programming Language）运行时** - 一种基于 YAML 格式的面向对象编程语言解释器。

## 特性

- 📝 **YAML 语法** - 使用人类可读的 YAML 格式编写代码
- 🏗️ **面向对象** - 支持类、继承和对象实例化
- 🔄 **动态类型** - 无需显式类型声明
- 📦 **模块系统** - 文件包含和标准库导入
- 🛠️ **标准库** - 内置 math、io、json、os、time 等模块
- 🐛 **调试工具** - 内置错误分析和调试功能

## 安装

```bash
pip install hpl-runtime
```

## 快速开始

创建 `hello.hpl` 文件：

```yaml
main: () => {
    echo "Hello, HPL!"
  }

call: main()
```

运行程序：

```bash
hpl hello.hpl
```

## 完整示例

```yaml
classes:
  Calculator:
    add: (a, b) => {
        return a + b
      }

objects:
  calc: Calculator()

main: () => {
    result = calc.add(10, 20)
    echo "Result: " + result
  }

call: main()
```

## 使用标准库

```yaml
imports:
  - math
  - io

main: () => {
    echo "PI: " + math.PI
    echo "sqrt(16): " + math.sqrt(16)
    io.write_file("test.txt", "Hello from HPL!")
  }

call: main()
```

## 文档

- [HPL 语法概览](https://github.com/TheSingularityStudio/HPL/blob/main/docs/HPL语法概览.md)
- [HPL 语法手册](https://github.com/TheSingularityStudio/HPL/blob/main/docs/HPL语法手册.md)

## 项目链接

- **主页**: https://github.com/TheSingularityStudio/HPL
- **问题反馈**: https://github.com/TheSingularityStudio/HPL/issues

## 许可证

[MIT License](LICENSE)
