# HPL 编程语言

> **H** 编程语言 - 基于 YAML 的面向对象动态类型编程语言

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](../LICENSE)

---

## 🚀 简介

**HPL（H Programming Language）** 是一种基于 YAML 格式的面向对象编程语言，使用动态类型系统。它提供简洁的语法和强大的功能，适合快速原型开发和脚本编写。

```yaml
# 你的第一个 HPL 程序
main: () => {
    echo "Hello, HPL!"
  }

call: main()
```

---

## ✨ 核心特性

| 特性 | 描述 |
|------|------|
| 📄 **YAML 语法** | 使用人类可读的 YAML 格式编写代码，易于学习和维护 |
| 🏗️ **面向对象** | 支持类、继承和对象实例化 |
| 🔄 **动态类型** | 无需显式类型声明，自动类型推断 |
| 📦 **丰富数据类型** | 整数、浮点数、字符串、布尔值、数组、字典 |
| 🎮 **控制流** | 条件语句、循环（for、while）、异常处理 |
| 📚 **模块系统** | 支持文件包含和标准库导入 |
| 🛠️ **标准库** | 内置 math、io、json、os、time 等模块 |
| 🐛 **错误处理** | 详细的错误信息和调用栈跟踪 |

---

## 🎯 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/TheSingularityStudio/HPL.git
cd HPL

# 安装依赖
pip install -r requirements.txt
```

### 运行示例

```bash
python hpl_runtime/interpreter.py examples/example.hpl
```

### 编写程序

创建 `hello.hpl`：

```yaml
main: () => {
    echo "Hello, HPL!"
  }

call: main()
```

运行：
```bash
python hpl_runtime/interpreter.py hello.hpl
```

---

## 📖 文档导航

| 页面 | 描述 |
|------|------|
| [🏠 首页](https://github.com/TheSingularityStudio/HPL/wiki) | 语言介绍和快速开始 |
| [📚 文档](https://github.com/TheSingularityStudio/HPL/wiki/Docs) | 完整语法参考和 API 文档 |
| [❓ 帮助](https://github.com/TheSingularityStudio/HPL/wiki/Help) | 错误代码详解与解决方案 |

---

## 💡 代码示例

### 基础示例

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
    echo "结果: " + result
  }

call: main()
```

### 使用标准库

```yaml
imports:
  - math
  - io

main: () => {
    # 数学模块
    pi = math.PI
    sqrt_result = math.sqrt(16)
    echo "PI: " + pi
    echo "sqrt(16): " + sqrt_result

    # IO 模块
    io.write_file("output.txt", "Hello from HPL!")
    content = io.read_file("output.txt")
    echo "文件内容: " + content
  }

call: main()
```

### 猜数字游戏

```yaml
imports:
  - time
  - math

main: () => {
    secret = math.floor(time.now() % 100) + 1
    attempts = 0

    echo "欢迎来到猜数字游戏！"

    while (true) :
      guess = int(input("请输入你的猜测（1-100）: "))
      attempts = attempts + 1

      if (guess == secret) :
        echo "恭喜你猜对了！用了 " + attempts + " 次尝试。"
        break
      else :
        if (guess < secret) :
          echo "太小了！"
        else :
          echo "太大了！"
  }

call: main()
```

---

## 🏗️ 项目结构

```
HPL/
├── hpl_runtime/          # 运行时核心
│   ├── core/            # 核心组件（词法、语法、执行）
│   ├── modules/         # 模块系统
│   ├── stdlib/          # 标准库
│   └── utils/           # 工具函数
├── examples/            # 示例程序
├── docs/                # 文档
│   ├── wiki/           # Wiki 文档
│   │   ├── home.md     # 首页
│   │   ├── help.md     # 帮助
│   │   └── doc.md      # 文档
│   ├── HPL语法概览.md   # 语法概览
│   └── HPL语法手册.md   # 详细手册
├── tests/               # 测试套件
└── README.md            # 项目说明
```

---

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -am 'Add new feature'`
4. 推送分支：`git push origin feature/new-feature`
5. 提交 Pull Request

---

## 📄 许可证

本项目采用 [MIT 许可证](../LICENSE) - 查看 LICENSE 文件了解详情。

---

> **提示**: HPL 基于 YAML 格式，缩进非常重要（建议使用 2 个空格）！

**[➡️ 继续阅读语法文档](https://github.com/TheSingularityStudio/HPL/wiki/docs)**
