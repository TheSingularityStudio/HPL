# HPL EXE 程序使用说明文档

## 目录
1. [简介](#简介)
2. [系统要求](#系统要求)
3. [获取 HPL.exe](#获取-hplexe)
4. [基本使用方法](#基本使用方法)
5. [高级功能](#高级功能)
6. [文件结构说明](#文件结构说明)
7. [故障排除](#故障排除)
8. [常见问题 FAQ](#常见问题-faq)
9. [使用示例](#使用示例)

---

## 简介

**HPL.exe** 是 HPL（H Programming Language）编程语言的独立可执行文件启动器。它允许您无需安装 Python 环境即可直接运行 `.hpl` 脚本文件。

### 主要特性

- ✅ **单文件可执行程序** - 无需安装，即开即用
- ✅ **拖放支持** - 直接将 `.hpl` 文件拖放到程序上运行
- ✅ **命令行支持** - 支持命令行参数调用
- ✅ **路径兼容** - 支持包含空格的文件路径
- ✅ **调试模式** - 内置调试信息输出功能
- ✅ **自动路径检测** - 智能查找运行时环境

---

## 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 7/8/10/11 (64位推荐) |
| 内存 | 最低 512 MB，推荐 2 GB 以上 |
| 磁盘空间 | 约 10 MB（包含运行时） |
| 依赖项 | 无需额外安装 Python 或其他依赖 |

---

## 获取 HPL.exe

### 方法一：下载预编译版本

从项目发布页面下载最新版本的 `HPL.exe` 文件。

### 方法二：自行构建

如果您有 Python 环境，可以从源码构建：

```bash
# 1. 克隆或下载项目源码
git clone https://github.com/TheSingularityStudio/HPL.git
cd HPL

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行构建脚本
python build_exe.py
```

构建完成后，`HPL.exe` 将位于 `dist/` 目录中。

### 构建过程说明

构建脚本 `build_exe.py` 会：
1. 检查并安装 PyInstaller（如未安装）
2. 打包所有 HPL 运行时模块
3. 包含标准库模块（math、io、json、os、time 等）
4. 生成单文件可执行程序
5. 显示输出文件路径和大小

---

## 基本使用方法

### 方法一：拖放运行（推荐）

最简单的使用方式：

1. 找到您的 `.hpl` 脚本文件
2. 将文件**拖放**到 `HPL.exe` 图标上
3. 程序自动运行并显示结果
4. 按回车键退出

### 方法二：命令行运行

打开命令提示符（CMD）或 PowerShell：

```cmd
# 基本用法
HPL.exe <hpl文件路径>

# 示例
HPL.exe examples\hello.hpl
HPL.exe "C:\Users\Name\Documents\my_script.hpl"
HPL.exe ..\project\main.hpl
```

### 方法三：设置文件关联

将 `.hpl` 文件类型关联到 `HPL.exe`：

1. 右键点击任意 `.hpl` 文件
2. 选择"打开方式" → "选择其他应用"
3. 浏览并选择 `HPL.exe`
4. 勾选"始终使用此应用打开 .hpl 文件"

---

## 高级功能

### 调试模式

当程序运行出现问题时，可以启用调试模式查看详细信息：

**命令行方式：**
```cmd
set HPL_DEBUG=1
HPL.exe your_script.hpl
```

**PowerShell 方式：**
```powershell
$env:HPL_DEBUG=1
HPL.exe your_script.hpl
```

调试模式将显示：
- 命令行参数解析情况
- 文件路径处理过程
- `hpl_runtime` 目录查找过程
- 模块加载状态
- 详细的错误堆栈信息

### 环境变量

| 环境变量 | 说明 | 示例 |
|---------|------|------|
| `HPL_DEBUG` | 启用调试输出 | `set HPL_DEBUG=1` |

### 路径处理规则

HPL.exe 支持多种路径格式：

```cmd
# 绝对路径
HPL.exe C:\Projects\script.hpl

# 相对路径
HPL.exe ..\script.hpl
HPL.exe .\examples\test.hpl

# 包含空格的路径（自动处理）
HPL.exe "C:\My Projects\script.hpl"
HPL.exe 'C:\My Projects\script.hpl'
```

---

## 文件结构说明

### 标准目录结构

```
您的项目目录/
├── HPL.exe              # 主程序（可放在任意位置）
├── hpl_runtime/         # 运行时目录（必须与exe同目录或内置）
│   ├── __init__.py
│   ├── interpreter.py
│   ├── core/            # 核心解析和执行模块
│   ├── stdlib/          # 标准库模块
│   ├── modules/         # 模块系统
│   └── utils/           # 工具函数
└── your_script.hpl      # 您的HPL脚本
```

### 运行时查找策略

HPL.exe 使用以下顺序查找 `hpl_runtime` 目录：

1. **打包资源路径** - PyInstaller 打包的临时目录
2. **程序所在目录** - `HPL.exe` 所在的文件夹
3. **当前工作目录** - 运行命令时的目录
4. **Python 路径** - 系统 Python 路径中的目录

### 部署方式

**方式一：便携模式（推荐）**
```
任意目录/
├── HPL.exe
└── hpl_runtime/         # 复制运行时目录
```

**方式二：系统路径模式**
将 `HPL.exe` 添加到系统 PATH 环境变量，随处可用。

---

## 故障排除

### 问题一：提示"无法找到 hpl_runtime 目录"

**症状：**
```
错误: 无法找到hpl_runtime目录
请确保hpl_runtime目录与HPL.exe在同一目录下
```

**解决方案：**

1. 确认 `hpl_runtime` 文件夹与 `HPL.exe` 在同一目录
2. 检查文件夹名称是否正确（区分大小写）
3. 重新运行构建脚本：
   ```bash
   python build_exe.py
   ```

### 问题二：拖放文件后无反应或闪退

**症状：** 拖放文件后窗口一闪而过，看不到输出。

**解决方案：**

1. **启用调试模式**查看详细错误：
   ```cmd
   set HPL_DEBUG=1
   HPL.exe your_file.hpl
   ```

2. **检查文件路径**：
   - 确认文件扩展名是 `.hpl`
   - 确认文件存在且未损坏
   - 尝试使用命令行运行查看错误信息

3. **检查文件编码**：
   - 确保文件使用 UTF-8 编码保存
   - 避免使用特殊字符作为文件名

### 问题三：模块导入错误

**症状：**
```
错误: 无法加载HPL解释器 - No module named 'xxx'
```

**解决方案：**

1. 重新构建 EXE 确保所有模块正确打包：
   ```bash
   python build_exe.py
   ```

2. 检查 `requirements.txt` 中的依赖是否完整安装：
   ```bash
   pip install -r requirements.txt
   ```

### 问题四：YAML 解析错误

**症状：**
```
YAML 解析错误: ...
```

**解决方案：**

1. 检查 HPL 文件语法是否正确
2. 确保 YAML 缩进使用空格而非制表符
3. 验证文件编码为 UTF-8
4. 使用在线 YAML 验证工具检查语法

---

## 常见问题 FAQ

### Q1: HPL.exe 可以在 Linux/Mac 上运行吗？

**A:** 目前 HPL.exe 仅支持 Windows 系统。Linux/Mac 用户需要直接使用 Python 运行解释器：

```bash
python hpl_runtime/interpreter.py your_script.hpl
```

### Q2: 如何更新 HPL.exe 到最新版本？

**A:** 
1. 下载最新的源码
2. 重新运行 `python build_exe.py`
3. 用新生成的 `HPL.exe` 替换旧版本

### Q3: 为什么我的脚本运行很慢？

**A:** 
- 首次运行可能需要解压运行时资源，稍等片刻
- 大型脚本建议拆分为多个模块使用 `include` 导入
- 避免在循环中进行大量 IO 操作

### Q4: 可以将 HPL.exe 和脚本一起打包分发吗？

**A:** 可以！这是推荐的分发方式：
```
您的项目/
├── HPL.exe
├── hpl_runtime/
└── scripts/
    ├── main.hpl
    └── utils.hpl
```

### Q5: 如何创建桌面快捷方式？

**A:**
1. 右键 `HPL.exe` → "发送到" → "桌面快捷方式"
2. 右键快捷方式 → "属性"
3. 在"目标"后添加您的脚本路径：
   ```
   C:\Path\HPL.exe C:\Path\your_script.hpl
   ```

### Q6: 支持哪些文件编码？

**A:** HPL.exe 支持 UTF-8 编码的文件。建议使用 VS Code、Notepad++ 等编辑器保存为 UTF-8 格式。

### Q7: 如何查看 HPL 版本信息？

**A:** 目前版本信息内置于构建时间。查看项目 `README.md` 或源码仓库获取版本号。

---

## 使用示例

### 示例 1：运行 Hello World

创建 `hello.hpl`：
```yaml
main: () => {
    echo "Hello, World!"
  }

call: main()
```

运行：
```cmd
HPL.exe hello.hpl
```

输出：
```
正在运行: D:\Projects\hello.hpl
--------------------------------------------------
Hello, World!

按回车键退出...
```

### 示例 2：使用标准库

创建 `math_demo.hpl`：
```yaml
imports:
  - math
  - io

main: () => {
    # 数学运算
    pi = math.PI
    sqrt_result = math.sqrt(16)
    echo "PI = " + pi
    echo "sqrt(16) = " + sqrt_result
    
    # 文件操作
    io.write_file("output.txt", "Hello from HPL!")
    content = io.read_file("output.txt")
    echo "文件内容: " + content
  }

call: main()
```

运行：
```cmd
HPL.exe math_demo.hpl
```

### 示例 3：调试模式运行

```cmd
set HPL_DEBUG=1
HPL.exe examples\debug_demo.hpl
```

输出示例：
```
[DEBUG] sys.argv = ['hpl_launcher.py', 'examples\\debug_demo.hpl']
[DEBUG] 参数数量: 2
[DEBUG] 处理后的文件路径: D:\HPL\examples\debug_demo.hpl
[DEBUG] 文件是否存在: True
正在运行: D:\HPL\examples\debug_demo.hpl
--------------------------------------------------
[DEBUG] 尝试运行文件: D:\HPL\examples\debug_demo.hpl
[DEBUG] 当前工作目录: D:\HPL
[DEBUG] 找到hpl_runtime目录: D:\HPL\hpl_runtime
...
```

### 示例 4：批处理运行多个脚本

创建 `run_all.bat`：
```batch
@echo off
echo 正在运行测试脚本...

HPL.exe test1.hpl
HPL.exe test2.hpl
HPL.exe test3.hpl

echo 所有脚本执行完成！
pause
```

---

## 技术支持

如遇到无法解决的问题，请：

1. 查看项目文档：`docs/` 目录
2. 参考示例程序：`examples/` 目录
3. 运行测试脚本：`python quick_test.py`
4. 提交 Issue 到项目仓库

---

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| 1.0 | 2026 | 初始版本，支持基本拖放和命令行运行 |
| 1.1 | 2026 | 增强路径处理，支持空格路径；添加调试模式 |

---

**文档版本：** 1.1  
**最后更新：** 2026年  
**适用程序版本：** HPL.exe 1.0+
