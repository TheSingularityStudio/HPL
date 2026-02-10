# HPL

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

HPL（H Programming Language）是一种基于 YAML 格式的面向对象编程语言，使用动态类型系统。它提供简洁的语法和强大的功能，适合快速原型开发和脚本编写。

## 特性

- **基于 YAML**：使用人类可读的 YAML 格式编写代码
- **面向对象**：支持类、继承和对象实例化
- **动态类型**：无需显式类型声明
- **丰富的数据类型**：整数、浮点数、字符串、布尔值、数组、字典
- **控制流**：条件语句、循环（for、while）、异常处理
- **模块系统**：支持文件包含和标准库导入
- **标准库**：内置 math、io、json、os、time 等模块
- **错误处理**：详细的错误信息和调用栈跟踪

## 安装

### 系统要求

- Python 3.6+
- PyYAML

### 安装步骤

1. 克隆仓库：
   ```bash
   git clone https://github.com/TheSingularityStudio/HPL.git
   cd hpl
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. （可选）构建可执行文件：
   ```bash
   python build_exe.py
   ```

## 快速开始

### 运行示例

运行内置示例：
```bash
python hpl_runtime/interpreter.py examples/example.hpl
```

### 编写第一个 HPL 程序

创建文件 `hello.hpl`：

```yaml
main: () => {
    echo "Hello, HPL!"
  }

call: main()
```

运行程序：
```bash
python hpl_runtime/interpreter.py hello.hpl
```

### 语法文档

- **[HPL 语法概览](docs/HPL语法概览.md)**：快速入门指南，包含基本语法和示例
- **[HPL 语法手册](docs/HPL语法手册.md)**：详细的语法参考，包括所有特性和标准库

## 解释器架构

HPL 解释器采用模块化设计，使用 Python 实现。架构包括以下组件：

- `models.py`: 定义数据模型，如 HPLClass、HPLObject、HPLFunction 等，用于表示类、对象和函数。
- `lexer.py`: 词法分析器，将源代码字符串转换为 Token 列表，支持行号和列号跟踪。
- `parser.py`: 使用 PyYAML 解析 YAML 文件，将其转换为内部表示形式。
- `ast_parser.py`: AST 解析器，将 Token 列表转换为抽象语法树。
- `evaluator.py`: 执行解析后的结构，处理方法调用、控制流和内置函数。
- `interpreter.py`: 主入口点，加载 YAML 文件，初始化组件并运行程序。

## 项目结构

```
hpl/
├── hpl_runtime/          # 运行时核心
│   ├── core/            # 核心组件
│   │   ├── models.py    # 数据模型
│   │   ├── lexer.py     # 词法分析器
│   │   ├── parser.py    # 解析器
│   │   ├── ast_parser.py # AST 解析器
│   │   ├── evaluator.py # 执行器
│   │   └── __init__.py
│   ├── modules/         # 模块系统
│   │   ├── base.py      # 基础模块
│   │   ├── loader.py    # 模块加载器
│   │   └── package_manager.py # 包管理器
│   ├── stdlib/          # 标准库
│   │   ├── io.py        # IO 模块
│   │   ├── json_mod.py  # JSON 模块
│   │   ├── math.py      # 数学模块
│   │   ├── os_mod.py    # OS 模块
│   │   └── time_mod.py  # 时间模块
│   └── utils/           # 工具函数
│       └── exceptions.py # 异常处理
├── examples/            # 示例程序
│   ├── example.hpl      # 基础示例
│   ├── guess_number.hpl # 猜数字游戏
│   └── test_*.hpl       # 测试文件
├── docs/                # 文档
│   ├── HPL语法概览.md    # 语法概览
│   └── HPL语法手册.md    # 详细手册
├── tests/               # 测试套件
├── build_exe.py         # 可执行文件构建脚本
├── build_package.py     # 包构建脚本
├── hpl_launcher.py      # 启动器
├── pyproject.toml       # 项目配置
├── requirements.txt     # 依赖列表
├── LICENSE              # 许可证
└── README.md           # 项目说明
```

## 示例程序

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
    echo "Result: " + result
  }

call: main()
```

### 使用标准库

```yaml
imports:
  - math
  - io

main: () => {
    # 使用数学模块
    pi = math.PI
    sqrt_result = math.sqrt(16)
    echo "PI: " + pi
    echo "sqrt(16): " + sqrt_result

    # 使用 IO 模块
    io.write_file("output.txt", "Hello from HPL!")
    content = io.read_file("output.txt")
    echo "File content: " + content
  }

call: main()
```

更多示例请查看 `examples/` 目录。

## 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -am 'Add new feature'`
4. 推送分支：`git push origin feature/new-feature`
5. 提交 Pull Request

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
python -m pytest tests/

# 运行特定测试
python tests/run_tests.py
```

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。
