# DeepWiki 无嵌入模式配置说明

## 修改完成 ✅

我已经修改了代码，现在 DeepWiki **无需配置任何嵌入模型**也能运行！

### 主要修改

1. **`api/main.py`** - 移除强制 API Key 检查
2. **`api/config.py`** - 添加 `is_rag_enabled()` 函数
3. **`api/config/embedder.json`** - 默认禁用嵌入模型
4. **`api/tools/embedder.py`** - 返回 None 当 RAG 禁用
5. **`api/simple_chat.py`** - 条件性使用 RAG

### 启动步骤

#### 1. 创建环境变量文件

复制模板文件：

```bash
copy .env.example .env
```

然后编辑 `.env`，填入至少一个 LLM 提供商的 API 密钥：

```env
# 只配置 Google Gemini (推荐)
GOOGLE_API_KEY=你的密钥

# 或者配置 OpenAI
OPENAI_API_KEY=你的密钥

# 或者配置 Ollama (本地免费)
OLLAMA_HOST=http://localhost:11434

# 嵌入模型设为 none（已默认设置）
DEEPWIKI_EMBEDDER_TYPE=none
```

#### 2. 安装依赖

**前端：**
```bash
yarn install
```

**后端：**
```bash
cd api
pip install poetry==2.0.1
poetry install
```

#### 3. 启动应用

**Windows:**
```bash
start.bat
```

**或手动启动：**

终端 1（后端）：
```bash
cd api
poetry run python -m api.main
```

终端 2（前端）：
```bash
yarn dev
```

### 功能对比

| 功能 | 有嵌入模型 (RAG) | 无嵌入模型 |
|------|-----------------|-----------|
| Wiki 文档生成 | ✅ 完整支持 | ✅ 完整支持 |
| 代码问答 | ✅ 精准定位代码 | ⚠️ 基于 LLM 记忆 |
| 架构图生成 | ✅ 支持 | ✅ 支持 |
| 文件内容查看 | ✅ 支持 | ✅ 支持 |

### 获取 API 密钥

- **Google Gemini**: https://makersuite.google.com/app/apikey (免费)
- **OpenAI**: https://platform.openai.com/api-keys
- **OpenRouter**: https://openrouter.ai/keys

### 故障排除

**问题：启动时报错 "No module named 'api'"**
- 确保在 `api` 目录的父目录运行命令

**问题：前端无法连接后端**
- 检查 `.env` 中的 `PORT` 是否为 8001
- 检查是否有防火墙阻止

**问题：LLM 报错**
- 确认 API 密钥正确
- 检查 API 密钥是否有额度

### 技术说明

无嵌入模式下，系统会：
1. 跳过代码向量化和 FAISS 索引构建
2. 问答时直接使用 LLM，不检索相关代码片段
3. 保留所有 Wiki 生成和可视化功能

这意味着你可以生成漂亮的代码文档和图表，但无法对代码进行精准的语义问答。
