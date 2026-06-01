# Aliyun Coding Plan (DashScope) 集成完成

## 新增功能

支持阿里云 DashScope Coding Plan 端点，使用 Anthropic API 格式。

## 配置信息

### 端点
```
https://coding.dashscope.aliyuncs.com/apps/anthropic/v1
```

### 认证方式
- `x-api-key`: DashScope API Key
- `Authorization: Bearer <key>`
- `anthropic-version: 2023-06-01`

### 支持模型
- `kimi-k2.5` (默认)
- `qwen3.6-plus`
- `glm-5`

## 环境变量

```env
# 使用 DASHSCOPE_API_KEY 作为 API Key
DASHSCOPE_API_KEY=your-dashscope-api-key

# 可选：自定义端点（默认已配置）
ALIYUN_CODING_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic/v1
```

## 修改文件列表

| 文件 | 修改内容 |
|------|---------|
| `api/aliyun_coding_client.py` | 新增 Aliyun Coding Plan 客户端 |
| `api/config.py` | 添加 AliyunCodingClient 导入和 CLIENT_CLASSES 映射 |
| `api/config/generator.json` | 添加 aliyun_coding provider 配置 |
| `api/simple_chat.py` | 添加 aliyun_coding 处理逻辑 |
| `api/websocket_wiki.py` | 添加 aliyun_coding 导入 |
| `.env.example` | 添加 Aliyun Coding 配置说明 |
| `src/messages/en.json` | 添加 providerAliyun_coding 翻译 |
| `src/messages/zh.json` | 添加 providerAliyun_coding 翻译 |

## 使用方法

1. 在 `.env` 文件中配置 `DASHSCOPE_API_KEY`
2. 启动应用
3. 在模型选择下拉框中选择 "Aliyun Coding"
4. 选择模型（kimi-k2.5、qwen3.6-plus 或 glm-5）

## 特点

- 使用 Anthropic API 格式（/messages 端点）
- 需要 `max_tokens` 参数（默认 4096）
- 非流式响应（当前实现）
- 支持自定义模型名称

## 参考

基于 openhuman 项目 commit 98940603 实现：
- https://help.aliyun.com/zh/dashscope/
- https://coding.dashscope.aliyuncs.com/apps/anthropic/v1
