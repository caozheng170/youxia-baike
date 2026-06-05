---
title: 游侠百科
emoji: 📖
colorFrom: green
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# 游侠百科 — 无限视觉浏览器

输入一个主题 → AI 生成一张信息图（infographic）→ 点击图上任意位置，继续深入探索那个细节。
灵感来自 [flipbook.page](https://flipbook.page)，可完全本地部署。

---

## 功能特性

- 🔍 **主题搜索**：输入任意主题，生成一张结构化信息图
- 👆 **点击探索**：点击图上某处，AI 理解你的意图并生成更深入的一张图
- 🧭 **路径导航**：搜索框同时充当多级导航栏，保留完整探索路径，可在各级之间自由来回切换
- 🔀 **模型一键切换**：界面右上角在「本地」与「线上 API」之间实时切换，无需重启。选择**随每个请求发送**，多用户互不干扰（适合公网部署）
- 🎨 **统一画风**：固定的"等距方格纸 + 水墨淡彩"画风模板，图内文字统一英文（避免中文乱码）
- 🔗 **分享 / 下载**：每页有独立链接，可下载为 PNG

---

## 技术路线

### 整体架构

```
┌──────────────┐   SSE 流式   ┌───────────────┐   OpenAI 兼容   ┌──────────────────┐
│  React + Vite │ ◄─────────► │ FastAPI 后端   │ ◄────────────► │   AI 模型服务      │
│   前端 (3000) │   REST API   │  (Python 8000) │   HTTP/JSON     │ 本地 / 线上 / Mock │
└──────────────┘             └───────────────┘                └──────────────────┘
```

- **前端**：React 18 + Vite。开发服务器把 `/api` 反向代理到后端 `:8000`。
- **后端**：FastAPI。所有生成接口用 **SSE（Server-Sent Events）** 流式返回，先回意图/预览、再回完整大图。
- **模型层**：三种 provider 适配器，均走 **OpenAI 兼容接口**，可运行时切换。

### 生成流水线（核心）

短主题不会直接丢给生图模型，而是先经过一层 **LLM 提示词扩写**，再叠加固定画风，最终才生图：

```
用户输入主题
   │
   ├─（文本 LLM 扩写）→ 选版式(路线图/时间轴/流程图/对比/图表/层级) + 填真实内容 + 英文标签
   │
   ├─（叠加固定画风 house style）→ 等距插画 / 方格纸底 / 水墨淡彩 / 引线标签 …
   │
   └─（生图模型）→ 完整大图 → PIL 缩小生成预览图 → 落盘 → SSE 推送
```

**点击探索（/api/explore）的流式时序：**

1. `intent` 事件：多模态模型先理解"你点了什么"，立刻把意图文本推给前端（点击点旁浮窗显示）
2. `preview` 事件：生成完成后推送预览图 + 页面元数据 + 导航路径
3. `full` 事件：推送完整大图

> 说明：为兼容线上 Agnes（不支持小尺寸/双图）且节省时间与费用，**每页只生成一张大图**，预览图由后端用 Pillow 缩小得到。

### 目录结构

```
flipbook/
├── server/                     # 后端 (FastAPI)
│   ├── main.py                 # 应用入口 + 所有 API 端点
│   ├── config.py               # 读取 .env 的配置
│   ├── models/                 # 生图模型适配器
│   │   ├── __init__.py         # ImageModel 抽象基类
│   │   ├── mock_model.py       # Mock 占位图（Pillow 本地绘制）
│   │   ├── local_model.py      # 本地 Xinference 适配器
│   │   └── cloud_model.py      # 线上 OpenAI 兼容适配器（含尺寸吸附）
│   ├── understanding/
│   │   └── multimodal.py       # 点击理解（Mock/本地/线上 多模态）
│   ├── prompt/
│   │   ├── builder.py          # 提示词模板（扩写失败时的回退）
│   │   └── enricher.py         # LLM 提示词扩写 + 固定画风 house style
│   └── storage/
│       └── store.py            # 页面持久化（JSON 元数据 + PNG 文件）
├── client/                     # 前端 (React + Vite)
│   ├── vite.config.js          # 端口 3000，/api 代理到 8000
│   └── src/
│       ├── App.jsx
│       ├── components/         # SearchBar / ProviderSwitch / PageView / ClickOverlay / ActionBar
│       ├── hooks/usePageGenerator.js   # 生成/探索/导航状态管理
│       └── api/client.js       # 封装 SSE 与 REST 调用
├── data/pages/                 # 运行时生成的数据（元数据 + images/ + previews/）
├── .env                        # 模型配置（含密钥，已被 .gitignore 忽略）
└── README.md
```

---

## 环境要求

- **Python** 3.10+（推荐 3.11）
- **Node.js** 18+（推荐 20/22）
- 后端依赖：`fastapi` `uvicorn` `pillow` `httpx` `pydantic` `python-dotenv`

---

## 快速开始

### Windows（PowerShell）

```powershell
# 1) 后端：建虚拟环境并装依赖
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install fastapi uvicorn pillow httpx pydantic python-dotenv

# 2) 启动后端（端口 8000）
.\.venv\Scripts\python.exe -m uvicorn server.main:app --reload --port 8000

# 3) 前端（另开一个终端）
cd client
npm install
npm run dev
```

### macOS / Linux（bash）

```bash
# 一键启动（自动装依赖并同时拉起前后端）
./start.sh
```

或手动：

```bash
pip install fastapi uvicorn pillow httpx pydantic python-dotenv
uvicorn server.main:app --reload --port 8000

cd client && npm install && npm run dev
```

启动后访问：

- 前端页面：<http://localhost:3000>
- 后端接口文档：<http://localhost:8000/docs>

---

## 参数配置

所有配置通过项目根目录的 **`.env`** 文件提供（后端启动时自动加载）。

### 模型来源

| 变量 | 取值 | 说明 |
|------|------|------|
| `MODEL_PROVIDER` | `mock` / `local` / `cloud` | 启动时的默认来源。运行时也可在界面右上角切换 |

- `mock`：本地用 Pillow 画占位图，**无需联网、开箱即用**，适合调试 UI。
- `local`：调用本地 Xinference（自有算力，免费）。
- `cloud`：调用线上 Agnes API。

### 本地模型（Xinference，OpenAI 兼容）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LOCAL_XINFERENCE_URL` | `http://localhost:9997` | 服务地址（代码内自动追加 `/v1/...`） |
| `LOCAL_API_KEY` | 空 | 鉴权 Key（Bearer） |
| `LOCAL_IMAGE_MODEL` | `Z-Image-Turbo` | 生图模型 |
| `LOCAL_VL_MODEL` | `qwen3.6-1` | 点击理解用的多模态模型 |
| `LOCAL_LLM_MODEL` | `qwen3.6-1` | 提示词扩写用的文本模型 |

### 线上模型（Agnes apihub，OpenAI 兼容）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CLOUD_BASE_URL` | `https://apihub.agnes-ai.com/v1` | 接口根地址（需含 `/v1`） |
| `CLOUD_API_KEY` | 空 | 鉴权 Key（Bearer） |
| `CLOUD_IMAGE_MODEL` | `agnes-image-2.1-flash` | 生图模型 |
| `CLOUD_VL_MODEL` | `agnes-1.5-flash` | 点击理解用的多模态模型（**必须支持图片输入**；`agnes-2.0-flash` 是纯文本，不可用于此） |
| `CLOUD_TEXT_MODEL` | `agnes-2.0-flash` | 提示词扩写用的文本模型 |

> ⚠️ **Agnes 生图尺寸**：线上仅支持 `1024x768` / `1024x1024` / `768x1024`。
> 代码会自动把请求尺寸"吸附"到最接近的支持尺寸（横版→`1024x768`）。

### 服务与存储

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HOST` | `0.0.0.0` | 监听地址 |
| `PORT` | `8000` | 后端端口 |
| `STORAGE_DIR` | `./data/pages` | 页面数据存储目录 |

图片尺寸常量在 `server/config.py`：完整图 `1280x720`，预览图 `640x360`（线上会按上面的规则吸附）。

### `.env` 示例

```ini
MODEL_PROVIDER=cloud

# 本地（Xinference）
LOCAL_XINFERENCE_URL=http://172.17.1.100:9997
LOCAL_API_KEY=sk-xxxxxxxx
LOCAL_IMAGE_MODEL=Z-Image-Turbo
LOCAL_VL_MODEL=qwen3.6-1
LOCAL_LLM_MODEL=qwen3.6-1

# 线上（Agnes）
CLOUD_BASE_URL=https://apihub.agnes-ai.com/v1
CLOUD_API_KEY=sk-xxxxxxxx
CLOUD_IMAGE_MODEL=agnes-image-2.1-flash
CLOUD_VL_MODEL=agnes-1.5-flash
CLOUD_TEXT_MODEL=agnes-2.0-flash
```

---

## API 一览

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET`  | `/api/health` | 健康检查，返回当前 provider |
| `GET`  | `/api/config` | 获取默认 provider 与可选列表（前端用作初始选项） |
| `POST` | `/api/config` | 设置**服务端默认** provider（可选；按请求传入的 provider 优先级更高） |
| `POST` | `/api/generate` | 主题生成（SSE：`preview` → `full`）。body 可带 `provider` |
| `POST` | `/api/explore` | 点击探索（SSE：`intent` → `preview` → `full`）。body 可带 `provider` |
| `GET`  | `/api/page/{id}` | 页面元数据 |
| `GET`  | `/api/page/{id}/image` | 完整大图 |
| `GET`  | `/api/page/{id}/preview` | 预览图 |
| `GET`  | `/api/share/{id}` | 分享数据 |
| `GET`  | `/api/pages` | 列出所有页面（调试用） |

---

## 常见问题

- **图里文字是英文？**
  有意为之。多数生图模型对中文渲染容易乱码，因此图内文字统一用英文（界面/导航仍是中文）。

- **线上生图较慢（约 1 分钟一张）？**
  Agnes 免费但出图偏慢，生成期间界面会显示加载动效。本地 `Z-Image-Turbo` 通常更快，可在右上角切到「本地」。

- **改了画风/提示词在哪改？**
  画风模板与扩写逻辑都集中在 `server/prompt/enricher.py`（单一来源，改一处全局生效）。

- **`start.sh` 在 Windows 跑不了？**
  它是 bash 脚本。Windows 请按上面的 PowerShell 步骤分别启动前后端。

---

## 部署上线

前后端**分开部署**：前端是静态站点（Netlify），后端是常驻 Python 进程（需支持 SSE 长连接，因此 **不要用 Serverless / Netlify Functions**）。

### 1. 后端（FastAPI，Docker）

仓库根目录已提供 `Dockerfile` / `requirements.txt` / `.dockerignore`，可直接部署到 **Hugging Face Spaces（Docker 模式）** / Render / Fly.io / Railway / 自有 VPS。

容器监听端口优先取环境变量 `PORT`，缺省 `7860`（贴合 HF Spaces 默认）。所需环境变量见 `.env.example`，**密钥务必通过平台的环境变量配置，不要写进镜像或提交进仓库**：

- `MODEL_PROVIDER`：服务端默认来源（`mock` / `local` / `cloud`）
- `CLOUD_BASE_URL` / `CLOUD_API_KEY` / `CLOUD_IMAGE_MODEL` / `CLOUD_VL_MODEL` / `CLOUD_TEXT_MODEL`
- 若要用本地模型：`LOCAL_XINFERENCE_URL` 等（注意公网平台访问不到你内网的 `172.x` 地址，仅内网/自有 VPS 可用）

> **Hugging Face Spaces**：新建 Space → SDK 选 **Docker** → 把仓库推上去；在 Space 的 `README.md` 头部 YAML 里写 `app_port: 7860`，在 Settings → Variables and secrets 里填上面的密钥。
>
> **Render**：New → Web Service → Docker，Render 会自动注入 `PORT`，环境变量同上。

本地也可直接用 Docker 验证：

```bash
docker build -t youxia-baike .
docker run -p 7860:7860 --env-file .env youxia-baike
# 打开 http://localhost:7860/docs
```

### 2. 前端（Netlify）

根目录已提供 `netlify.toml`（`base=client`、`publish=dist`、SPA 回退）。在 Netlify 关联仓库即可自动构建，**唯一要做的**是在 Site settings → Environment variables 设置后端地址：

```
VITE_API_BASE = https://你的后端域名      # 例如 https://your-space.hf.space
```

构建时前端会把所有 API 请求指向 `${VITE_API_BASE}/api`。后端已开启 CORS（允许跨域），SSE 直连即可工作。

- 本地开发：`VITE_API_BASE` 留空 → 请求走 `/api`，由 Vite 代理到 `localhost:8000`（见 `client/.env.example`）。
- 生产：必须设置 `VITE_API_BASE` 指向后端，否则前端会找不到 `/api`。

### 部署注意事项

- **存储是临时的**：免费平台容器重启后 `data/pages` 会清空（生成的页面/分享链接失效）。需要持久化请挂载磁盘或接对象存储。
- **冷启动**：免费档常有休眠，首个请求可能等待数十秒唤醒。
- **线上出图较慢**：Agnes 约 1 分钟一张，属正常现象。
- **本地开关保留**：内网用户仍可在界面切到「本地」直连自有算力。

---

## License

MIT
