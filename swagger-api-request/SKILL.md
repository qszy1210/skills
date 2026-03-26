---
name: swagger-api-request
description: >-
  Search and explore Swagger/OpenAPI documentation via MCP tools: list API modules,
  search endpoints by keyword, get full API details with parameters and cURL examples.
  Use when the user needs to find an API endpoint, understand request/response format,
  generate API request code, or asks about Swagger documentation — such as "搜索用户
  相关接口", "获取某接口的请求参数", "生成调用代码".
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

## MCP Server 信息

- **Server 名称**: `swagger`（在 MCP 配置中注册的名称）
- **传输方式**: stdio
- **项目路径**: `/Users/qs/vibe/mcp-swagger`
- **入口**: `node /Users/qs/vibe/mcp-swagger/dist/index.js`
- **必填环境变量**: `SWAGGER_BASE_URL`

## 可用工具

### 1. `swagger_list_modules` — 列出所有 Swagger 模块

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `refresh` | boolean | 否 | 是否强制刷新缓存 |

**返回**: 模块名称、标题、版本、API 数量、标签列表。

**适用场景**：初次了解系统有哪些服务模块；不确定接口在哪个模块下。

### 2. `swagger_search_api` — 关键词搜索接口

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `keyword` | string | 是 | 搜索关键词（匹配路径、名称、描述、标签） |
| `module` | string | 否 | 限定模块名称，缩小搜索范围 |

**返回**: 匹配的 API 列表（路径、方法、摘要、所属模块）。

**适用场景**：用户描述了功能需求但不知道具体接口路径。

### 3. `swagger_get_api_detail` — 获取接口详情

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `path` | string | 是 | API 路径，如 `/api/user/info` |
| `method` | string | 否 | HTTP 方法（GET/POST/PUT/DELETE），不填则返回所有方法 |
| `module` | string | 否 | 模块名称 |

**返回**: 完整参数表、响应格式、cURL 示例。

**适用场景**：已知接口路径，需要了解完整请求规范；生成调用代码前获取参数信息。

### 4. `swagger_clear_cache` — 清除文档缓存

无参数。

**适用场景**：后端接口有更新，需要获取最新文档。

## 使用策略

### 典型工作流

```
1. 不知道接口在哪里？
   → swagger_list_modules() 先看模块概览

2. 知道功能关键词？
   → swagger_search_api(keyword="用户登录")

3. 知道具体路径？
   → swagger_get_api_detail(path="/api/auth/login", method="POST")

4. 接口文档过时？
   → swagger_clear_cache() 然后重新查询
```

### 搜索技巧

- **中文搜索**：`swagger_search_api(keyword="用户")` — 匹配接口的中文描述
- **路径片段**：`swagger_search_api(keyword="/user/")` — 按路径搜索
- **限定模块**：`swagger_search_api(keyword="login", module="auth-service")` — 缩小范围
- **搜索无果时**：先用 `swagger_list_modules()` 确认可用模块，再尝试不同关键词

### 生成代码流程

当用户要求生成 API 调用代码时：

1. 用 `swagger_search_api` 找到目标接口
2. 用 `swagger_get_api_detail` 获取完整参数和响应定义
3. 根据返回的参数表和响应格式生成代码（TypeScript/Python/cURL 等）
4. cURL 示例可直接从工具返回值中获取

### 注意事项

- 该工具基于 **Swagger 2.0**（`/swagger-resources` + `definitions`），对纯 OpenAPI 3.0 后端可能解析不完整
- 搜索采用**大小写不敏感的子串匹配**
- `swagger_get_api_detail` 的 `path` 参数支持**子串匹配**（双向包含），无需精确路径
