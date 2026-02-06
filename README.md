# HPL
一种基于YAML格式的面向对象的编程语言的运行器

## 解释器架构

HPL 解释器采用模块化设计，使用 Python 实现。架构包括以下组件：

- `models.py`: 定义数据模型，如 HPLClass、HPLObject、HPLFunction 等，用于表示类、对象和函数。
- `parser.py`: 使用 PyYAML 解析 YAML 文件，将其转换为内部表示形式。
- `evaluator.py`: 执行解析后的结构，处理方法调用、控制流和内置函数。
- `interpreter.py`: 主入口点，加载 YAML 文件，初始化组件并运行程序。

### 依赖
- PyYAML: 用于解析 YAML 文件。

### 使用
运行解释器：`python interpreter.py <hpl_file>`

例如：`python interpreter.py example.hpl`
