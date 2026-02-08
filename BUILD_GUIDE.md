# HPL启动器打包指南

## 快速开始

### 方法一：使用打包脚本（推荐）

```bash
python build_exe.py
```

该脚本会自动：
1. 检查并安装PyInstaller
2. 打包HPL启动器为exe
3. 设置HPL.jpeg为图标
4. 包含src目录作为依赖

### 方法二：手动打包

```bash
# 安装PyInstaller
pip install pyinstaller

# 打包命令
python -m PyInstaller --onefile --noconsole --name HPL --icon HPL.jpeg --add-data "src;src" hpl_launcher.py
```

## 打包参数说明

| 参数 | 说明 |
|------|------|
| `--onefile` | 打包为单个exe文件 |
| `--noconsole` | 不显示控制台窗口 |
| `--name HPL` | 输出文件名为HPL.exe |
| `--icon HPL.jpeg` | 设置程序图标 |
| `--add-data "src;src"` | 包含src目录（Windows用;分隔） |
| `--clean` | 清理临时文件 |

## 输出文件

打包完成后，exe文件位于：
```
dist/HPL.exe
```

## 使用方法

### 1. 命令行运行
```bash
HPL.exe examples/example.hpl
HPL.exe C:\path\to\your\file.hpl
```

### 2. 拖放运行
将.hpl文件拖放到HPL.exe上即可运行

### 3. 文件关联（可选）

创建文件关联后，可以双击.hpl文件直接运行：

1. 右键点击.hpl文件
2. 选择"打开方式" → "选择其他应用"
3. 浏览到HPL.exe
4. 勾选"始终使用此应用打开.hpl文件"

## 注意事项

1. **图标格式**：HPL.jpeg会被自动转换为ico格式，如果打包时报错，可以手动转换：
   ```bash
   # 安装Pillow
   pip install Pillow
   
   # 转换图标（在Python中）
   from PIL import Image
   img = Image.open('HPL.jpeg')
   img.save('HPL.ico', format='ICO', sizes=[(256,256), (128,128), (64,64), (32,32), (16,16)])
   ```

2. **依赖问题**：如果打包后运行报错，可能是src目录未正确包含。检查：
   - 确保src目录与hpl_launcher.py在同一目录
   - 打包时使用`--add-data "src;src"`参数

3. **防病毒软件**：某些防病毒软件可能误报PyInstaller打包的exe，这是正常现象。

## 故障排除

### 问题1：打包失败
- 确保已安装PyInstaller：`pip install pyinstaller`
- 检查HPL.jpeg是否存在
- 检查src目录是否存在

### 问题2：运行时报"找不到src目录"
- 确保打包时使用了`--add-data`参数
- 检查dist目录中是否包含src文件夹

### 问题3：图标未显示
- Windows可能需要刷新图标缓存
- 重启资源管理器或重启电脑

## 高级配置

### 修改exe元信息

创建`HPL.spec`文件（PyInstaller配置文件），添加版本信息：

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['hpl_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('src', 'src')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HPL',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='HPL.jpeg',
    version='version.txt',  # 版本信息文件
)
```

创建`version.txt`：
```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'奇点工作室'),
        StringStruct(u'FileDescription', u'HPL解释器'),
        StringStruct(u'FileVersion', u'1.0.0'),
        StringStruct(u'InternalName', u'HPL'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2024'),
        StringStruct(u'OriginalFilename', u'HPL.exe'),
        StringStruct(u'ProductName', u'HPL编程语言'),
        StringStruct(u'ProductVersion', u'1.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
```

然后使用spec文件打包：
```bash
python -m PyInstaller HPL.spec
