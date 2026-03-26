# 实施计划：创建 metadata-query 和 swagger-api-request Skills

## 概述

将 `mcp-metadata` 和 `mcp-swagger` 两个 MCP Server 项目的知识转化为 Cursor Agent Skills，放在 `/Users/qs/github/skills/` 仓库下。

**目标**：让 AI Agent 在特定场景下自动触发对应 Skill，正确使用 MCP 工具完成任务。

---

## 执行须知（执行会话必读）

### 自包含原则

本计划**完全自包含**。执行时：

- **不要**读取或引用原始 MCP 项目文件（`/Users/qs/vibe/mcp-metadata/`、`/Users/qs/vibe/mcp-swagger/`）
- **不要**去查看原始项目的 README、源码或配置
- 每个 Stage 的 SKILL.md 内容已在本计划中**完整提供**，直接使用即可
- 所有需要的上下文（工具名、参数、使用场景）均已内联在本计划中

### 进度标记规则

每完成一个 Stage，**必须**更新本文件中对应的 Status 字段：

```
**Status**: ✅ Complete    →  完成后改为
**Status**: ✅ Complete
```

如果某个 Stage 正在进行中：

```
**Status**: ✅ Complete    →  改为
**Status**: 🔄 In Progress
```

如果遇到问题需要跳过：

```
**Status**: ✅ Complete    →  改为
**Status**: ⚠️ Blocked — [原因简述]
```

**操作方式**：使用编辑工具直接修改本文件 `/Users/qs/github/skills/docs/IMPLEMENTATION_PLAN.md` 中对应 Stage 的 Status 行。

### 执行流程

1. 读取本计划
2. 按 Stage 顺序执行（Stage 1 → Stage 2 → Stage 3）
3. 每个 Stage 开始前，将 Status 改为 `🔄 In Progress`
4. 每个 Stage 完成后，将 Status 改为 `✅ Complete`
5. 完成所有 Stage 后，在文件末尾追加完成记录（见下方模板）

### 完成记录模板

所有 Stage 完成后，在本文件末尾追加：

```markdown
---

## 执行记录

- **执行时间**: [当前日期时间]
- **执行结果**: 全部完成 / 部分完成
- **备注**: [如有问题或调整，记录在此]
```

---

## Stage 1: 创建 metadata-query Skill

**Goal**: 创建 `metadata-query/SKILL.md`，指导 Agent 在需要理解元数据、对象结构、字段详情时使用 MCP metadata 工具。

**目标路径**: `/Users/qs/github/skills/metadata-query/SKILL.md`

**Status**: ✅ Complete

### 操作步骤

#### 1.1 创建目录

```bash
mkdir -p /Users/qs/github/skills/metadata-query
```

#### 1.2 创建 SKILL.md

写入以下**完整内容**到 `/Users/qs/github/skills/metadata-query/SKILL.md`：

````markdown
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
````

### 验证

- [ ] 文件路径正确：`/Users/qs/github/skills/metadata-query/SKILL.md`
- [ ] YAML frontmatter 中 `name` 和 `description` 存在且非空
- [ ] 文件总行数 < 500 行
- [ ] description 包含触发关键词（object, field, metadata, 字段, 对象, 字典）

---

## Stage 2: 创建 swagger-api-request Skill

**Goal**: 创建 `swagger-api-request/SKILL.md`，指导 Agent 在需要查询 Swagger API 文档、了解接口参数、生成请求代码时使用 MCP swagger 工具。

**目标路径**: `/Users/qs/github/skills/swagger-api-request/SKILL.md`

**Status**: ✅ Complete

### 操作步骤

#### 2.1 创建目录

```bash
mkdir -p /Users/qs/github/skills/swagger-api-request
```

#### 2.2 创建 SKILL.md

写入以下**完整内容**到 `/Users/qs/github/skills/swagger-api-request/SKILL.md`：

````markdown
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
````

### 验证

- [ ] 文件路径正确：`/Users/qs/github/skills/swagger-api-request/SKILL.md`
- [ ] YAML frontmatter 中 `name` 和 `description` 存在且非空
- [ ] 文件总行数 < 500 行
- [ ] description 包含触发关键词（swagger, API, endpoint, 接口, 请求, cURL）

---

## Stage 3: 验证与提交

**Goal**: 验证两个 Skill 文件结构正确，提交到 git。

**Status**: ✅ Complete

### 操作步骤

#### 3.1 验证文件结构

```bash
# 确认目录结构
ls -la /Users/qs/github/skills/metadata-query/
ls -la /Users/qs/github/skills/swagger-api-request/

# 确认行数 < 500
wc -l /Users/qs/github/skills/metadata-query/SKILL.md
wc -l /Users/qs/github/skills/swagger-api-request/SKILL.md
```

#### 3.2 验证 YAML frontmatter

```bash
# 检查 frontmatter 是否完整（应以 --- 开头和结尾）
head -10 /Users/qs/github/skills/metadata-query/SKILL.md
head -10 /Users/qs/github/skills/swagger-api-request/SKILL.md
```

#### 3.3 提交 Skills

```bash
cd /Users/qs/github/skills
git add metadata-query/ swagger-api-request/
git commit -m "feat: add metadata-query and swagger-api-request skills

- metadata-query: guide agent to use MCP metadata tools for enterprise
  object types, fields, schemas, dictionaries
- swagger-api-request: guide agent to use MCP swagger tools for API
  search, detail retrieval, and cURL generation"
```

#### 3.4 更新本计划的 Status 并提交

将本文件中 Stage 1、Stage 2、Stage 3 的 Status 全部标记为 `✅ Complete`，在末尾追加执行记录，然后提交：

```bash
cd /Users/qs/github/skills
git add docs/IMPLEMENTATION_PLAN.md
git commit -m "docs: mark implementation plan as complete"
```

### 验证清单

- [ ] `metadata-query/SKILL.md` 存在且格式正确
- [ ] `swagger-api-request/SKILL.md` 存在且格式正确
- [ ] 两个文件 YAML frontmatter 都包含 `name` 和 `description`
- [ ] 两个文件行数均 < 500
- [ ] description 使用第三人称，包含 WHAT 和 WHEN
- [ ] 无 Windows 路径、无过时信息、术语一致
- [ ] git commit 成功
- [ ] 本计划文件中所有 Stage Status 已标记为 ✅ Complete
- [ ] 本计划文件末尾已追加执行记录

---

## 附录：命名决策

| 项目 | Skill 名称 | 命名理由 |
|------|-----------|----------|
| mcp-metadata | `metadata-query` | "query" 表达主要用途是查询元数据；避免 "mcp-" 前缀因为 skill 使用者无需关心底层是 MCP |
| mcp-swagger | `swagger-api-request` | "api-request" 表达主要用途是查找和理解 API 请求规范；"swagger" 保留因为是触发关键词 |

## 附录：MCP Server 配置参考

执行 Skill 前，确保 Cursor MCP 配置中已注册对应 Server。

### metadata server

```json
{
  "mcpServers": {
    "metadata": {
      "command": "node",
      "args": ["/Users/qs/vibe/mcp-metadata/build/index.js"],
      "env": {
        "MCP_API_BASEURL": "http://your-api-server:port",
        "MCP_USERNAME": "your-username",
        "MCP_PASSWORD": "your-password"
      }
    }
  }
}
```

### swagger server

```json
{
  "mcpServers": {
    "swagger": {
      "command": "node",
      "args": ["/Users/qs/vibe/mcp-swagger/dist/index.js"],
      "env": {
        "SWAGGER_BASE_URL": "http://your-swagger-server:port",
        "SWAGGER_COOKIES": "",
        "SWAGGER_HEADERS": "{\"knife4j-gateway-code\":\"ROOT\"}"
      }
    }
  }
}
```

---

## 执行记录

- **执行时间**: 2026-03-26 16:55
- **执行结果**: 全部完成
- **备注**: 两个 Skills 已创建并提交到 git (commit db3db71)
  - metadata-query/SKILL.md: 134 行
  - swagger-api-request/SKILL.md: 113 行
