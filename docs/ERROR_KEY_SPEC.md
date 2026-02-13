# HPL Error Key 规范文档

## 概述

Error Key 用于对错误进行分类，支持错误国际化和自动化处理。所有通过 `_create_error()` 创建的错误都应包含 error_key。

## 命名规范

Error Key 使用大写字母，采用 `CATEGORY_SUBCATEGORY_DETAIL` 格式。

### 分类前缀

| 前缀 | 说明 | 示例 |
|------|------|------|
| `RUNTIME_` | 运行时错误 | `RUNTIME_DIVISION_BY_ZERO` |
| `TYPE_` | 类型错误 | `TYPE_INVALID_OPERATION` |
| `SYNTAX_` | 语法错误 | `SYNTAX_UNEXPECTED_TOKEN` |
| `IMPORT_` | 导入错误 | `IMPORT_MODULE_NOT_FOUND` |
| `IO_` | IO错误 | `IO_READ_ERROR` |
| `NAME_` | 名称错误 | `NAME_UNDEFINED_VARIABLE` |

## 完整Error Key列表

### 运行时错误 (RUNTIME_*)

| Error Key | 说明 | 使用场景 |
|-----------|------|----------|
| `RUNTIME_GENERAL` | 通用运行时错误 | 未知语句类型、未知表达式类型等 |
| `RUNTIME_DIVISION_BY_ZERO` | 除零错误 | 除法或取模运算中除数为0 |
| `RUNTIME_INDEX_OUT_OF_BOUNDS` | 索引越界 | 数组/字符串索引超出有效范围 |
| `RUNTIME_KEY_NOT_FOUND` | 键不存在 | 字典中访问不存在的键 |
| `RUNTIME_UNDEFINED_VAR` | 未定义变量 | 访问未定义的变量或函数 |
| `RUNTIME_RECURSION_LIMIT` | 递归深度超限 | 递归调用超过最大深度 |

### 类型错误 (TYPE_*)

| Error Key | 说明 | 使用场景 |
|-----------|------|----------|
| `TYPE_INVALID_OPERATION` | 无效操作 | 对不支持的类型执行操作 |
| `TYPE_MISSING_PROPERTY` | 属性不存在 | 访问对象不存在的属性 |
| `TYPE_CONVERSION_FAILED` | 类型转换失败 | int()/float()等转换失败 |
| `TYPE_MISMATCH` | 类型不匹配 | 操作数类型不兼容 |

### 语法错误 (SYNTAX_*)

| Error Key | 说明 | 使用场景 |
|-----------|------|----------|
| `SYNTAX_UNEXPECTED_TOKEN` | 意外标记 | 遇到未预期的token |
| `SYNTAX_INVALID_INDENT` | 缩进错误 | 缩进级别不正确 |
| `SYNTAX_MISSING_BRACKET` | 缺少括号 | 括号不匹配 |

### 导入错误 (IMPORT_*)

| Error Key | 说明 | 使用场景 |
|-----------|------|----------|
| `IMPORT_MODULE_NOT_FOUND` | 模块未找到 | 无法找到指定模块 |
| `IMPORT_CIRCULAR` | 循环导入 | 检测到循环导入 |
| `IMPORT_SYNTAX_ERROR` | 导入语法错误 | import语句语法错误 |

### IO错误 (IO_*)

| Error Key | 说明 | 使用场景 |
|-----------|------|----------|
| `IO_READ_ERROR` | 读取错误 | 文件读取失败 |
| `IO_WRITE_ERROR` | 写入错误 | 文件写入失败 |
| `IO_EOF` | 文件结束 | 意外到达文件末尾 |

## 使用示例

```python
# 正确的error_key使用
raise self._create_error(
    HPLTypeError,
    "Cannot perform operation on type",
    line=expr.line,
    column=expr.column,
    local_scope=local_scope,
    error_key='TYPE_INVALID_OPERATION'
)

# 运行时错误
raise self._create_error(
    HPLRuntimeError,
    "Division by zero",
    line=stmt.line,
    column=stmt.column,
    local_scope=local_scope,
    error_key='RUNTIME_DIVISION_BY_ZERO'
)
```

## 添加新Error Key的流程

1. 确定错误分类（RUNTIME/TYPE/SYNTAX/IMPORT/IO）
2. 使用描述性名称，格式为 `CATEGORY_DETAIL`
3. 在此文档中添加说明
4. 在代码中使用新的error_key
5. 更新相关测试

## 注意事项

- 所有error_key必须唯一
- 使用已有的error_key，避免重复创建
- 保持命名一致性
- 文档和代码同步更新
