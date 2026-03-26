---
name: metadata-query
description: >-
  Query enterprise metadata via MCP tools: object types, fields, field schemas,
  field data ranges, object relationships, and dictionary data. Use when the user
  asks about object structure, field details, data models, enum values, dictionary
  lookups, or any question requiring knowledge of the enterprise data schema —
  such as "XX 对象有哪些字段", "字段可选值是什么", "对象之间的关系", "字典数据".
---

# 企业元数据查询

## 触发条件

当用户提问涉及以下内容时使用：

| 场景 | 示例问题 |
|------|----------|
| 理解对象结构 | "User 对象有哪些字段？"、"Order 对象的定义是什么？" |
| 字段详情 | "status 字段是什么类型？"、"这个字段是否必填？" |
| 字段可选值 | "User.status 的可选值有哪些？"、"枚举值是什么？" |
| 字段模式 | "string_field_schema 的验证规则是什么？" |
| 对象关系 | "Order 对象关联了哪些其他对象？" |
| 字典数据 | "系统有哪些字典？"、"获取所有字典数据" |
| 数据建模 | 生成表单、报表、接口时需要了解字段结构 |
| 缓存刷新 | 元数据更新后需要同步最新数据 |

## MCP Server 信息

- **Server 名称**: `metadata`（在 MCP 配置中注册的名称）
- **传输方式**: stdio
- **项目路径**: `/Users/qs/vibe/mcp-metadata`
- **入口**: `node /Users/qs/vibe/mcp-metadata/build/index.js`

## 可用工具

### 1. `get_metadata` — 获取全量元数据

获取所有元数据 bundle（ObjectType、Field、FieldSchema、ObjectRelationship）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `version` | string | 否 | 客户端缓存版本号；为空返回最新；与服务端一致则只返回版本号 |

**适用场景**：首次了解系统全貌、初始化缓存、版本对比。

**注意**：返回数据量大，优先使用更精确的工具（如 `get_object_fields`）。

### 2. `get_object_type_metadata` — 获取单个对象的元数据 bundle

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `objectTypeName` | string | 是 | 对象类型名称，如 `User`、`Order` |
| `withRefObject` | boolean | 否 | 是否包含引用对象的元数据，默认 false |

**适用场景**：需要了解某对象的完整信息（字段 + 模式 + 关系）。当用户问"XX 对象的完整元数据"时使用。

### 3. `get_object_type` — 获取对象类型基本信息

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `objectName` | string | 是 | 对象名称 |
| `withDetail` | boolean | 否 | 是否包含详细信息（字段列表等），默认 false |

**适用场景**：快速查看对象定义、标签、描述。

### 4. `get_object_fields` — 获取对象的所有字段

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `objectName` | string | 是 | 对象名称 |

**适用场景**：查看字段列表、类型、是否必填。生成表单或报表结构时首选。

### 5. `get_field_data_range` — 获取字段的数据范围/可选值

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `objectTypeName` | string | 是 | 对象类型名称 |
| `fieldName` | string | 是 | 字段名称 |

**适用场景**：了解枚举可选值、生成下拉选项、数据校验。

### 6. `get_field_schema` — 获取字段模式详情

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `fieldSchemaId` | string | 是 | 字段模式 ID |

**适用场景**：查看字段验证规则、显示格式、行为约束。

### 7. `refresh_metadata_cache` — 刷新服务端元数据缓存

无参数。

**适用场景**：元数据有更新后强制同步；故障排查时清除缓存。

### 8. `get_all_dict_data` — 获取所有字典数据

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `dictBaseUrl` | string | 否 | 字典服务地址，不提供则使用默认 API 地址 |

**适用场景**：查看系统字典、获取业务枚举值、理解数据取值范围。

## 使用策略

### 选择合适的工具

```
用户问"XX 对象有哪些字段？"
  → get_object_fields(objectName="XX")

用户问"XX.YY 字段的可选值？"
  → get_field_data_range(objectTypeName="XX", fieldName="YY")

用户问"XX 对象的完整元数据"
  → get_object_type_metadata(objectTypeName="XX", withRefObject=true)

用户问"获取字典数据"
  → get_all_dict_data()

用户问"刷新/更新元数据"
  → refresh_metadata_cache()
```

### 渐进式查询

对于复杂问题，按以下顺序逐步深入：

1. **先概览**：`get_object_type` 了解对象基本信息
2. **再看字段**：`get_object_fields` 获取字段列表
3. **再深入**：`get_field_data_range` 或 `get_field_schema` 查看具体字段细节
4. **看关联**：`get_object_type_metadata(withRefObject=true)` 了解对象间关系
