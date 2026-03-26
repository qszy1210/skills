---
name: swagger-api-request
description: >-
  Search and explore Swagger/OpenAPI documentation by directly fetching API docs
  from the server: list modules, search endpoints by keyword, get full API
  details with parameters and cURL examples. Use when the user needs to find an
  API endpoint, understand request/response format, generate API request code,
  or asks about Swagger documentation — such as "搜索用户相关接口", "获取某接口
  的请求参数", "生成调用代码".
---

# Swagger API 请求查询

## 触发条件

当用户提问涉及以下内容时使用：

| 场景 | 示例问题 |
|------|----------|
| 搜索接口 | "搜索用户登录相关的接口"、"有哪些 order 相关 API？" |
| 接口详情 | "获取 /api/user/info 的请求参数"、"POST /auth/login 的格式" |
| 生成请求代码 | "根据接口生成 TypeScript 请求函数"、"给我 cURL 命令" |
| 浏览模块 | "列出所有 API 模块"、"系统有哪些服务模块？" |
| 了解 API 结构 | "这个接口需要传哪些参数？"、"响应格式是什么？" |
| 集成开发 | 前端对接后端接口、编写 API 调用层时需要了解接口规范 |

## 前置条件：获取连接信息

首次查询 Swagger 文档前，必须获取服务信息。按以下流程操作：

### 步骤 1：向用户获取连接信息

向用户提问（使用 AskQuestion 工具或直接对话）：

```
需要以下信息来访问 Swagger 文档：
1. Swagger 服务地址（必填，如 http://192.168.1.104:30337）
2. 如果需要认证，请提供以下之一：
   - Cookie 字符串（从浏览器开发者工具 Network 面板复制）
   - 自定义请求头（如 {"knife4j-gateway-code":"ROOT"}）
```

### 步骤 2：记录凭据

在本次会话中记住以下变量，后续所有请求复用：

- `SWAGGER_BASE_URL`：用户提供的服务地址（必须有值）
- `COOKIES`：Cookie 字符串（可选）
- `CUSTOM_HEADERS`：自定义请求头键值对（可选）

### 获取 Cookie 的方法（告知用户）

如果用户不知道如何获取 Cookie：

1. 在浏览器中打开 Swagger 文档页面（如 `http://服务地址/doc.html`）
2. 完成登录
3. 按 F12 打开开发者工具 → Network 面板
4. 刷新页面，点击任意请求
5. 复制请求头中的 `Cookie` 值

## 通用请求格式

所有请求携带以下请求头：

```bash
curl -H "Accept: application/json" \
     -b "${COOKIES}" \
     -H "<自定义头key>: <自定义头value>" \
     "<url>"
```

无需认证时可省略 `-b` 和自定义头。

## 工作流程

### 第一步：获取模块列表

```bash
curl -s -H "Accept: application/json" \
     -b "${COOKIES}" \
     "${SWAGGER_BASE_URL}/swagger-resources"
```

返回 JSON 数组，示例：

```json
[
  { "name": "user-service", "url": "/v2/api-docs?group=user-service", "swaggerVersion": "2.0" },
  { "name": "order-service", "url": "/v2/api-docs?group=order-service", "swaggerVersion": "2.0" }
]
```

每项的 `name` 是模块名，`url` 是文档路径后缀。

### 第二步：获取模块 API 文档

用第一步返回的 `url` 拼接完整路径：

```bash
curl -s -H "Accept: application/json" \
     -b "${COOKIES}" \
     "${SWAGGER_BASE_URL}<resource.url>"
```

返回标准 Swagger 2.0 JSON，关键结构：

```json
{
  "info": { "title": "...", "version": "..." },
  "basePath": "/api",
  "paths": {
    "/user/info": {
      "get": {
        "tags": ["用户管理"],
        "summary": "获取用户信息",
        "parameters": [...],
        "responses": { "200": { "description": "OK", "schema": {...} } }
      }
    }
  },
  "definitions": { "UserVO": { "type": "object", "properties": {...} } }
}
```

### 第三步：搜索接口

从文档 JSON 的 `paths` 中搜索匹配的接口：

**匹配字段**（大小写不敏感的子串匹配）：
- 路径字符串
- `summary`（接口名称/摘要）
- `description`（接口描述）
- `tags`（标签）
- `operationId`（操作 ID）

### 第四步：提取接口详情

从匹配的 `paths[path][method]` 中提取：

| 信息 | 位置 |
|------|------|
| 参数列表 | `parameters` 数组 |
| 参数位置 | `parameters[].in`（`path`/`query`/`header`/`body`/`formData`） |
| 请求体模型 | `parameters` 中 `in=body` 的 `schema`，可能含 `$ref` |
| 响应格式 | `responses.200.schema` |
| 完整 URL | `${SWAGGER_BASE_URL}${basePath}${path}` |

### 解析 `$ref` 引用

`$ref` 格式为 `#/definitions/ModelName`，在文档的 `definitions` 字段中查找对应模型：

```json
{
  "$ref": "#/definitions/UserVO"
}
→ 查找 definitions.UserVO → { "type": "object", "properties": { "name": { "type": "string" }, ... } }
```

递归解析嵌套的 `$ref`，深度建议不超过 5 层。

### 第五步：生成 cURL 示例

根据提取的参数信息构造可执行的 cURL 命令：

```bash
curl -X POST '${SWAGGER_BASE_URL}${basePath}${path}' \
  -H 'Accept: application/json' \
  -H 'Content-Type: application/json' \
  -b '${COOKIES}' \
  -d '{ "根据 schema 生成的请求体" }'
```

## 使用策略

### 快速选择

```
用户问"系统有哪些模块/服务？"
  → curl .../swagger-resources

用户问"搜索 XX 相关接口"
  → 获取模块文档 → 遍历 paths 搜索关键词

用户问"获取某接口的详细参数"
  → 获取模块文档 → 定位 paths[path][method] → 提取 parameters

用户问"生成调用代码"
  → 获取接口详情 → 根据参数和 schema 生成代码
```

### 搜索技巧

- **中文搜索**：搜索 `summary`/`description` 中的中文描述
- **路径片段搜索**：在 `paths` 的 key 中搜索路径子串
- **限定模块**：只获取并搜索特定模块的文档，减少数据量
- **搜索无果时**：先列出模块（`/swagger-resources`），确认可用模块后再尝试

### 注意事项

- 该流程基于 **Swagger 2.0**（`/swagger-resources` + `definitions`），纯 OpenAPI 3.0 后端（`components.schemas`、`requestBody`）可能需调整解析逻辑
- `$ref` 仅支持 `#/definitions/ModelName` 格式
- 搜索采用**双向子串包含匹配**（路径包含关键词，或关键词包含路径）

### 完整调用示例

```bash
# 1. 列出所有模块
curl -s "${SWAGGER_BASE_URL}/swagger-resources" | python3 -m json.tool

# 2. 获取 user-service 模块文档
curl -s "${SWAGGER_BASE_URL}/v2/api-docs?group=user-service" -b "${COOKIES}" > swagger-doc.json

# 3. 搜索包含"login"的接口路径（从下载的文档中）
cat swagger-doc.json | python3 -c "
import json, sys
doc = json.load(sys.stdin)
for path, methods in doc.get('paths', {}).items():
    for method, op in methods.items():
        if method == 'parameters': continue
        text = f'{path} {op.get(\"summary\",\"\")} {op.get(\"description\",\"\")}'.lower()
        if 'login' in text:
            print(f'{method.upper()} {path} — {op.get(\"summary\",\"\")}')
"

# 4. 调用某个 API
curl -X POST "${SWAGGER_BASE_URL}/api/auth/login" \
     -H "Content-Type: application/json" \
     -b "${COOKIES}" \
     -d '{"username":"admin","password":"123456"}'
```
