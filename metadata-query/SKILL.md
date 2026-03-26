---
name: metadata-query
description: >-
  Query enterprise metadata REST API to retrieve object types, fields, field
  schemas, field data ranges, object relationships, and dictionary data. Use
  when the user asks about object structure, field details, data models, enum
  values, dictionary lookups, or any question requiring knowledge of the
  enterprise data schema — such as "XX 对象有哪些字段", "字段可选值是什么",
  "对象之间的关系", "字典数据".
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

## 前置条件：认证获取

首次调用 API 前，必须完成认证。按以下流程操作：

### 步骤 1：向用户获取连接信息

向用户提问（使用 AskQuestion 工具或直接对话）：

```
需要以下信息来访问元数据 API：
1. API 服务地址（如 http://192.168.1.104:30337）
2. 认证方式：
   - 方式 A：直接提供 Token
   - 方式 B：提供用户名和密码，由我自动登录获取 Token
```

### 步骤 2：获取 Token

**如果用户提供了 Token**：直接使用，跳到步骤 3。

**如果用户提供了用户名和密码**：调用登录接口获取 Token：

```bash
curl -s -X POST "${API_BASE_URL}/api/oauth/auth/login" \
  -H "Content-Type: application/json" \
  -H "X-Request-Platform: ZSSY_PORTAL" \
  -d '{
    "username": "<用户名>",
    "password": "<密码>",
    "smsCode": "123",
    "captchaId": "",
    "loginType": 1,
    "platform": "ZSSY_PORTAL",
    "clientType": "PC"
  }'
```

从响应 JSON 中提取 `accessToken` 字段值。

### 步骤 3：记录凭据

在本次会话中记住以下变量，后续所有 API 调用复用：

- `API_BASE_URL`：用户提供的服务地址
- `AUTH_TOKEN`：Token 值（来自用户直接提供或登录接口返回）
- `PLATFORM`：默认 `ZSSY_PORTAL`（除非用户指定其他值）
- `TENANT`：默认 `ZSTAX`（除非用户指定其他值）

## 通用请求格式

所有 API 请求必须携带以下请求头：

```bash
curl -H "Authorization: ${AUTH_TOKEN}" \
     -H "X-Request-Platform: ${PLATFORM}" \
     -H "X-Request-Tenant: ${TENANT}" \
     "<url>"
```

如果收到 HTTP 401 响应，说明 Token 已过期，需重新执行认证流程的步骤 2。

## API 端点

以下 `${BASE}` 代表 `API_BASE_URL` 的值。

### 1. 获取全量元数据

```
GET ${BASE}/api/enterprise/sys/metadata/bundle
GET ${BASE}/api/enterprise/sys/metadata/bundle?version=<版本号>
```

返回所有 ObjectType、Field、FieldSchema、ObjectRelationship。

**注意**：返回数据量大，优先使用更精确的端点。

### 2. 获取单个对象的元数据

```
GET ${BASE}/api/enterprise/sys/metadata/bundle/{objectTypeName}
GET ${BASE}/api/enterprise/sys/metadata/bundle/{objectTypeName}?withRefObject=true
```

返回指定对象的字段、字段模式和关系。`withRefObject=true` 时包含引用对象。

### 3. 获取对象类型基本信息

```
GET ${BASE}/api/enterprise/sys/metadata/objectTypes/{objectName}
GET ${BASE}/api/enterprise/sys/metadata/objectTypes/{objectName}?withDetail=true
```

返回对象的名称、标签、描述等基本信息。

### 4. 获取对象字段列表

```
GET ${BASE}/api/enterprise/sys/metadata/objectTypes/{objectName}/fields
```

返回对象的所有字段，包含字段名、类型、是否必填等信息。

### 5. 获取字段数据范围/可选值

```
GET ${BASE}/api/enterprise/sys/metadata/fieldDataRange/{objectTypeName}/{fieldName}
```

返回字段的可选值、枚举值或数据分布。

### 6. 获取字段模式详情

```
GET ${BASE}/api/enterprise/sys/metadata/fieldSchemas/{fieldSchemaId}
```

返回字段的验证规则、显示格式、行为约束。

### 7. 刷新服务端元数据缓存

```
POST ${BASE}/api/enterprise/sys/metadata/refreshCache
```

强制刷新服务端缓存，确保后续查询返回最新数据。

### 8. 获取字典数据

```
GET ${BASE}/api/authority/system/dict-data/list-all-simple
```

返回系统中所有简单字典数据。如果字典服务地址与元数据服务不同，替换 `${BASE}` 为字典服务地址。

## 使用策略

### 快速选择

```
用户问"XX 对象有哪些字段？"
  → GET .../objectTypes/XX/fields

用户问"XX.YY 字段的可选值？"
  → GET .../fieldDataRange/XX/YY

用户问"XX 对象的完整元数据"
  → GET .../bundle/XX?withRefObject=true

用户问"获取字典数据"
  → GET .../dict-data/list-all-simple

用户问"刷新元数据"
  → POST .../refreshCache
```

### 渐进式查询

对于复杂问题，按以下顺序逐步深入：

1. **先概览**：`GET .../objectTypes/{name}` 了解对象基本信息
2. **再看字段**：`GET .../objectTypes/{name}/fields` 获取字段列表
3. **再深入**：`GET .../fieldDataRange/...` 或 `GET .../fieldSchemas/...` 查看具体字段细节
4. **看关联**：`GET .../bundle/{name}?withRefObject=true` 了解对象间关系

### 调用示例

```bash
# 获取 User 对象的字段列表
curl -H "Authorization: ${AUTH_TOKEN}" \
     -H "X-Request-Platform: ZSSY_PORTAL" \
     -H "X-Request-Tenant: ZSTAX" \
     "${API_BASE_URL}/api/enterprise/sys/metadata/objectTypes/User/fields"

# 获取 User.status 字段的可选值
curl -H "Authorization: ${AUTH_TOKEN}" \
     -H "X-Request-Platform: ZSSY_PORTAL" \
     -H "X-Request-Tenant: ZSTAX" \
     "${API_BASE_URL}/api/enterprise/sys/metadata/fieldDataRange/User/status"

# 获取 Order 对象完整元数据（含引用对象）
curl -H "Authorization: ${AUTH_TOKEN}" \
     -H "X-Request-Platform: ZSSY_PORTAL" \
     -H "X-Request-Tenant: ZSTAX" \
     "${API_BASE_URL}/api/enterprise/sys/metadata/bundle/Order?withRefObject=true"
```
