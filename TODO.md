# HPL 错误处理改进实施计划 - Phase 2

## 阶段 2：开发者体验（已完成）

### 任务 4：智能错误建议 ✅

- [x] 创建 `hpl_runtime/utils/error_suggestions.py` - 智能建议引擎
  - [x] 实现 ErrorSuggestionEngine 类
  - [x] 添加常见拼写错误检测（print→pritn, function→fucntion 等）
  - [x] 实现相似名称查找（Levenshtein 距离）
  - [x] 添加类型错误模式识别
  - [x] 实现快速修复代码生成

- [x] 修改 `hpl_runtime/utils/exceptions.py` - 集成建议系统
  - [x] 添加 HPLKeyError 异常类
  - [x] 改进 get_error_suggestion() 函数
  - [x] 添加 format_error_with_suggestions() 函数

- [x] 修改 `hpl_runtime/utils/error_handler.py` - 支持建议引擎
  - [x] 添加建议引擎初始化
  - [x] 传递作用域信息到建议引擎
  - [x] 集成智能建议到错误报告

### 任务 5：增强错误消息 ✅

- [x] 改进数组/字典访问错误信息
  - [x] 添加 HPLKeyError 异常类
  - [x] 增强数组索引越界错误提示（显示有效范围、反向索引建议）
  - [x] 添加反向索引建议
  - [x] 显示可用字典键和相似键建议

- [x] 添加边界检查提示
  - [x] 索引边界提示（valid range: 0 to {length-1}）
  - [x] 除零检查示例
  - [x] 类型转换建议

- [x] 添加类型转换建议
  - [x] 显示实际 vs 期望类型
  - [x] 建议转换函数（int(), str(), float()）

## 当前进行中的任务
- [x] 创建 Phase 2 实施计划
- [x] 任务 4：智能错误建议（完成）
- [x] 任务 5：增强错误消息（完成）

## Phase 2 完成总结

### 新增文件
1. `hpl_runtime/utils/error_suggestions.py` - 智能错误建议引擎

### 修改的文件
1. `hpl_runtime/utils/exceptions.py` - 添加 HPLKeyError 和智能建议支持
2. `hpl_runtime/utils/error_handler.py` - 集成建议引擎
3. `hpl_runtime/core/evaluator.py` - 增强错误消息和上下文

### 主要功能
- 智能拼写检查和纠正建议
- 相似变量名查找
- 类型错误模式识别和修复建议
- 数组索引越界详细提示（包括反向索引建议）
- 字典键错误提示（包括相似键建议）
- 类型转换错误增强提示
- 除零错误修复建议
- 快速修复代码生成
