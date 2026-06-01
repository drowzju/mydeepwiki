# DeepWiki CLI Builder

命令行工具，无需浏览器即可生成 Wiki。默认使用 **Aliyun Coding** 的 **kimi-k2.5** 模型，无需嵌入模型即可运行。

## 特性

- 🚀 **实时进度显示** - 总体进度条 + 每页实时字符数
- ⏱️ **预计剩余时间** - 基于平均生成速度计算 ETA
- 🔴🟡🟢 **按重要性分类** - 高/中/低优先级页面可视化
- 🖥️ **后台运行** - 关闭终端也不会中断
- 💾 **自动保存** - 每页完成后自动保存到服务器缓存
- 📄 **本地导出** - 同时生成 Markdown 文件
- 🔄 **断点续传** - 支持重用服务器缓存
- ✅ **零配置启动** - 默认使用 Aliyun Coding kimi-k2.5，无需 API Key

## 安装

```bash
# 进入 cli 目录
cd cli

# 安装依赖
pip install -r requirements.txt

# 可选：添加到 PATH
chmod +x wiki-builder
export PATH="$PATH:$(pwd)"
```

## 使用方法

### 基本用法（推荐）

```bash
# 最简单的用法 - 零配置，使用默认 Aliyun Coding kimi-k2.5
python wiki_builder.py owner/repo

# 指定完整 URL
python wiki_builder.py https://github.com/owner/repo

# 生成中文 wiki
python wiki_builder.py owner/repo --language zh

# 生成详细版本（8-12页）
python wiki_builder.py owner/repo --comprehensive
```

### 使用其他模型

```bash
# 使用 OpenAI
python wiki_builder.py owner/repo --provider openai --model gpt-4

# 使用 Google
python wiki_builder.py owner/repo --provider google --model gemini-2.5-flash

# 使用 Ollama（本地）
python wiki_builder.py owner/repo --provider ollama --model llama3
```

### 基本用法

```bash
# 生成 GitHub 仓库的 wiki
python wiki_builder.py owner/repo

# 指定完整 URL
python wiki_builder.py https://github.com/owner/repo

# 生成本地仓库的 wiki
python wiki_builder.py /path/to/repo --type local

# 使用 OpenAI 模型
python wiki_builder.py owner/repo --provider openai --model gpt-4

# 生成中文 wiki
python wiki_builder.py owner/repo --language zh

# 生成详细版本
python wiki_builder.py owner/repo --comprehensive
```

### 高级用法

```bash
# 私有仓库（需要 token）
python wiki_builder.py owner/private-repo --token YOUR_GITHUB_TOKEN

# 自定义服务器地址
python wiki_builder.py owner/repo --server ws://192.168.1.100:8091

# 排除特定目录
python wiki_builder.py owner/repo --excluded-dirs "tests,docs,node_modules"

# 排除特定文件
python wiki_builder.py owner/repo --excluded-files "*.test.js,*.spec.py"

# 指定输出目录
python wiki_builder.py owner/repo -o ~/wikis

# 不保存到服务器缓存
python wiki_builder.py owner/repo --no-cache
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `repo` | 仓库地址（owner/repo、URL 或本地路径） | 必需 |
| `--type` | 仓库类型：github/gitlab/bitbucket/local | github |
| `--token` | 私有仓库访问令牌 | - |
| `--provider` | 模型提供商 | aliyun_coding |
| `--model` | 模型名称 | kimi-k2.5 |
| `--language` | 输出语言：en/zh/ja/es/kr/vi/fr/ru/pt-br | en |
| `--server` | WebSocket 服务器地址 | ws://localhost:8091 |
| `--comprehensive` | 生成详细版本（8-12页） | 否 |
| `--excluded-dirs` | 排除的目录（逗号分隔） | - |
| `--excluded-files` | 排除的文件（逗号分隔） | - |
| `-o, --output` | 输出目录 | 当前目录 |
| `--no-cache` | 不保存到服务器缓存 | 否 |
| `--rag` | 启用 RAG（需要 embedder，质量更高但更慢） | 否 |

## 示例

### 示例 1：最简单的用法（默认配置）

```bash
# 使用默认的 Aliyun Coding kimi-k2.5，无需任何配置
python wiki_builder.py facebook/react --language zh
```

### 示例 2：生成详细版本

```bash
python wiki_builder.py kubernetes/kubernetes \
  --comprehensive \
  --language zh \
  -o ~/wikis \
  --excluded-dirs "vendor,docs,_output"
```

### 示例 3：使用其他模型

```bash
# 使用 OpenAI GPT-4
python wiki_builder.py owner/repo --provider openai --model gpt-4 --language zh

# 使用 Google Gemini
python wiki_builder.py owner/repo --provider google --model gemini-2.5-flash --language zh

# 使用 Ollama（本地）
python wiki_builder.py owner/repo --provider ollama --model llama3 --language zh
```

### 示例 4：启用 RAG（更高质量，但需要 embedder）

```bash
# 需要先配置 embedder（如 Ollama）
export DEEPWIKI_EMBEDDER_TYPE=ollama
python wiki_builder.py owner/repo --rag --language zh
```

### 示例 5：后台运行

```bash
# 使用 nohup 后台运行
nohup python wiki_builder.py owner/repo --language zh > wiki.log 2>&1 &

# 或使用 screen
screen -S wiki
python wiki_builder.py owner/repo --language zh
# Ctrl+A+D  detach

# 之后重新连接
screen -r wiki
```

## 进度显示示例

运行时会显示实时进度：

```
╔══════════════════════════════════════════════════════════════════════╗
║                    DeepWiki CLI Builder v1.0                         ║
╠══════════════════════════════════════════════════════════════════════╣
║  Repository: https://github.com/facebook/react                       ║
║  Type:      github      Provider: google                           ║
║  Model:     gemini-2.5-flash         Language: zh                    ║
║  Output:    .                                                        ║
╚══════════════════════════════════════════════════════════════════════╝

======================================================================
STEP 1: Generating wiki structure...
======================================================================

✓ Generated wiki structure with 6 pages
  1. 🔴 项目概述与架构 (high)
  2. 🟡 核心Hooks详解 (medium)
  3. 🟡 组件生命周期 (medium)
  4. 🟢 性能优化指南 (low)
  5. 🟢 测试策略 (low)
  6. 🔴 贡献指南 (high)

======================================================================
STEP 2: Generating page contents...
======================================================================

📋 Total pages to generate: 6
   🔴 High: 2
   🟡 Medium: 2
   🟢 Low: 2

[1/6] 🔴 项目概述与架构
Overall |████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░| 0% ETA: --
  Generating 项目概述与架构... (2,458 chars received)
  ✓ Completed in 45s (3,892 chars)

[2/6] 🟡 核心Hooks详解
Overall |████████████████░░░░░░░░░░░░░░░░░░░░░░░| 16% ETA: 3m 45s
  Generating 核心Hooks详解... (1,234 chars received)
  ...

======================================================================
✓ All pages generated in 4m 32s
======================================================================

✓ Wiki saved to server cache successfully
✓ Wiki exported to: react_wiki_20240601_143052.md

======================================================================
                    🎉 Wiki generation complete! 🎉
======================================================================
```

## 工作原理

1. **连接后端**：通过 WebSocket 连接到 DeepWiki 后端服务
2. **生成结构**：首先生成 wiki 的目录结构（XML 格式）
3. **生成内容**：逐个页面生成详细内容
4. **保存缓存**：自动保存到服务器缓存（`~/.adalflow/wikicache/`）
5. **导出文件**：同时导出为本地 Markdown 文件

## 与浏览器的区别

| 特性 | CLI | 浏览器 |
|------|-----|--------|
| 需要保持连接 | 否（后台运行） | 是 |
| 断点续传 | 部分支持（可重用缓存） | 中断后需重新开始 |
| 可视化界面 | 无 | 有 |
| 批量导出 | 自动导出 Markdown | 需手动导出 |
| 适合场景 | 大仓库/批量处理 | 快速预览 |

## 注意事项

1. **确保后端服务已启动**：
   ```bash
   # 检查后端是否运行
   curl http://localhost:8091/health
   ```

2. **内存使用**：大仓库可能需要较多内存，建议在服务器上运行

3. **API 限制**：注意 LLM API 的速率限制

4. **缓存机制**：
   - 服务器缓存：`~/.adalflow/wikicache/`
   - 本地导出：当前目录或 `-o` 指定的目录

## 故障排查

### 连接失败

```bash
# 检查后端服务
curl http://localhost:8091/health

# 检查 WebSocket
python -c "import websockets; print('OK')"
```

### 生成中断

如果生成过程中断，可以：
1. 重新运行相同命令（会跳过已缓存的部分）
2. 使用 `--no-cache` 强制重新生成
3. 查看输出目录的 Markdown 文件（已完成的页面）

### 依赖问题

```bash
# 重新安装依赖
pip install --upgrade -r requirements.txt
```

## 开发计划

- [ ] 断点续传（从上次中断的页面继续）
- [ ] 进度条显示
- [ ] 多线程并行生成
- [ ] 配置文件支持
- [ ] 批量仓库处理
