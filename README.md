[**🇨🇳中文**](https://github.com/shibing624/llm-debate-arena/blob/main/README.md) | [**🌐English**](https://github.com/shibing624/llm-debate-arena/blob/main/README_EN.md)

<div align="center">
  <a href="https://github.com/shibing624/llm-debate-arena">
    <img src="https://github.com/shibing624/llm-debate-arena/blob/main/docs/favicon.svg" height="150" alt="Logo">
  </a>
</div>

-----------------

# LLM Debate Arena - AI辩论竞技场
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](README.md)
[![License Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![python_version](https://img.shields.io/badge/Python-3.10%2B-green.svg)](requirements.txt)
[![GitHub issues](https://img.shields.io/github/issues/shibing624/llm-debate-arena.svg)](https://github.com/shibing624/llm-debate-arena/issues)
[![Wechat Group](https://img.shields.io/badge/wechat-group-green.svg?logo=wechat)](#Contact)


**LLM Debate Arena**: AI辩论竞技场，竞技对抗型 AI 辩论挑战赛

LLM Debate Arena 是一个创新的 AI 辩论平台，让不同的大语言模型在辩论赛中一决高下。通过 ELO 排位系统、多裁判投票制和 SSE 实时流式展示，打造公平、有趣、专业的 AI 竞技体验。

### 核心特性

- ⚔️ **竞技对抗**: 任意两个模型 PK，支持同模型对战（不计ELO）
- 🏆 **ELO 排位**: 动态 ELO 算法，辩题难度系数加成
- 👨‍⚖️ **多裁判制**: 多位裁判投票，确保公平
- 🎭 **性格注入**: 5种辩论风格（理性/激进/温和/幽默/学术）
- 🔧 **工具增强**: Python解释器、网络搜索、计算器（可选，按需启用）
- 📊 **数据沉淀**: 完整历史记录、天梯榜、对战详情
- 🎬 **实时流式**: SSE 推送，辩论过程流畅展示
- 👤 **用户系统**: 注册登录、JWT 认证、个人历史记录
- 📝 **Markdown 渲染**: 支持富文本、表格、代码高亮展示
- 🎨 **现代化 UI**: React + Tailwind CSS + Framer Motion 动画

### 在线体验

🎮 **官方示例**: [https://debate.mulanai.com/](https://debate.mulanai.com/)


![image.png](https://github.com/shibing624/llm-debate-arena/blob/main/docs/main.png)


## 🚀 快速开始

### 方式一：Docker 部署（推荐）

使用 Docker Compose 一键启动：

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写 API Keys

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

服务将在 `http://localhost:8000` 启动。

> 📚 更多 Docker 部署细节，请参考 [Docker 部署指南](docs/DOCKER.md)

#### Docker 单独构建

```bash
# 构建镜像
docker build -t llm-debate-arena .

# 运行容器
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e OPENROUTER_API_KEY=your_api_key \
  -e AVAILABLE_MODELS=gpt-4o,gpt-4o-mini,claude-3.5-sonnet \
  --name debate-arena \
  llm-debate-arena
```

### 方式二：本地开发

#### 环境要求

- Python 3.10+
- Node.js 18+
- SQLite (默认) 或 PostgreSQL

#### 后端启动

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（复制 .env.example 为 .env 并填写）
cp ../.env.example ../.env

# 开发环境：启动后端服务
uvicorn backend.main:app --reload --port 8000 --host 0.0.0.0

# 生产环境：使用 gunicorn 启动（推荐）
nohup gunicorn backend.main:app -w 1 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --timeout 1000 > app.log 2>&1 &

# 注意：worker 数量建议设为 1，因为 SSE 长连接需要状态共享
```

后端服务运行在 `http://localhost:8000`

API 文档: `http://localhost:8000/docs`

#### 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 配置环境变量（复制 .env.example 为 .env）
cp .env.example .env
# 编辑 .env 文件：
# VITE_API_BASE_URL=http://localhost:8000  # 后端地址
# VITE_IS_DEV=true                         # 开发模式

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

前端服务运行在 `http://localhost:5173`

**前端技术栈：**
- React 18.2 + TypeScript 5.2
- Vite 5.0（快速构建工具）
- Tailwind CSS 3.3（原子化 CSS）
- Framer Motion 10.16（动画库）
- React Router v6.20（路由）
- React Markdown 9.0（Markdown 渲染，支持表格）
- Recharts 2.10（ELO 评分曲线图表）

#### 一键启动脚本

```bash
# 使用启动脚本（同时启动前后端）
sh start.sh
```

#### 命令行直接发起辩论（无需启动前端）

```bash
python main/mini_font/run_debate_cli.py
```

脚本会直接提示输入：
- 辩题
- 当前可用模型列表（随后从列表中选择）
- 正方模型 ID
- 反方模型 ID
- 局数
- 每局轮数


## 🔧 配置说明

### 环境变量

在 `.env` 文件中配置：

```env
# LLM API 配置
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_API_URL=https://api.openai.com/v1

# 可用模型列表（逗号分隔）
AVAILABLE_MODELS=gpt-4o,gpt-4o-mini,claude-3.5-sonnet,gpt-5.1

# 数据库配置
# SQLite（默认，适合开发和小规模部署）
DATABASE_URL=sqlite:///./debate_arena.db

# MySQL（推荐生产环境）
# DATABASE_URL=mysql+pymysql://user:password@host:3306/debate_arena?charset=utf8mb4

# Serper API (搜索工具)
SERPER_API_KEY=your_serper_api_key_here
```

> 📚 如需迁移到 MySQL，请参考 [MySQL 迁移指南](docs/MYSQL_MIGRATION.md)

### 前端环境变量

在 `frontend/.env` 文件中配置：

```env
# API Base URL - 后端服务地址
# - 如果设置了非默认值（非 http://localhost:8000），则始终使用此 URL
# - 如果未设置或为默认值：
#   - 开发环境（VITE_IS_DEV=true）：使用此 URL
#   - 生产环境（VITE_IS_DEV=false）：使用相对路径 /api（需要 Nginx 代理）
VITE_API_BASE_URL=http://localhost:8000

# 是否为开发环境
# true: 开发模式，直接访问 VITE_API_BASE_URL
# false: 生产模式，使用相对路径（需要 Nginx 代理）
VITE_IS_DEV=true
```

**前端配置说明：**
- **开发环境**（`VITE_IS_DEV=true`）：前端直接访问后端完整 URL（如 `http://localhost:8000/api/...`）
- **生产环境**（`VITE_IS_DEV=false`）：
  - 如果设置了自定义 `VITE_API_BASE_URL`（非默认值），则使用完整 URL
  - 否则使用相对路径（如 `/api/...`），需要 Nginx 反向代理
- 修改后端地址只需修改 `.env` 文件，无需改动代码

### 模型配置

通过 `AVAILABLE_MODELS` 环境变量添加可用模型：

- 格式：逗号分隔的模型 ID
- 示例：`gpt-4o,gpt-4o-mini,claude-3.5-sonnet,your-custom-model`
- 模型会自动初始化，`display_name` 为模型 ID 的大写形式
- 无需修改代码，重启服务即可生效


## 系统设计

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (React)                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 竞技场   │  │ 天梯榜   │  │ 注册     │  │ 登录     │   │
│  │ Arena    │  │ Leaderboard│ │ Register │  │ (Modal)  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │              │             │          │
│       └─────────────┴──────────────┴─────────────┘          │
│                     │ SSE / HTTP REST                       │
└─────────────────────┼───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                  后端 API (FastAPI)                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            /api/tournament/                          │  │
│  │  • POST /match/stream    (SSE流式比赛)               │  │
│  │  • GET  /leaderboard     (天梯榜)                    │  │
│  │  • GET  /matches/history (历史，支持筛选)            │  │
│  │  • GET  /match/{id}      (比赛详情)                  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            /api/auth/                                │  │
│  │  • POST /register        (注册)                      │  │
│  │  • POST /login           (登录，支持邮箱)            │  │
│  │  • GET  /me              (获取用户信息)              │  │
│  └──────────────────────────────────────────────────────┘  │
│                      ↓                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Tournament│  │  Judge   │  │   ELO    │  │   Auth   │  │
│  │ Manager  │→ │  Panel   │→ │  System  │  │   JWT    │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │             │              │             │          │
│       ↓             ↓              ↓             ↓          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐ │
│  │   LLM    │  │  Tools   │  │      Database            │ │
│  │  Client  │  │  Engine  │  │  (SQLAlchemy + SQLite)   │ │
│  └──────────┘  └──────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                    数据层 (SQLite)                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────┐│
│  │ competitors│  │  matches   │  │   topics   │  │ users ││
│  │  (模型)     │  │  (比赛)     │  │  (辩题)     │  │(用户)││
│  └────────────┘  └────────────┘  └────────────┘  └───────┘│
└─────────────────────────────────────────────────────────────┘
```

### ELO 排位系统

```
新分数 = 旧分数 + K因子 × 难度系数 × (实际得分 - 期望得分)

K因子 (动态):
- 新手期 (< 10场): 64
- 成长期 (10-30场): 32
- 成熟期 (> 30场): 16

难度系数:
- Easy: 0.8
- Medium: 1.0
- Hard: 1.5
- Expert: 2.0
```

### 多裁判投票制

1. 排除参赛选手作为裁判
2. 多位裁判独立打分（逻辑/证据/说服力）
3. 综合评分决定胜者
4. 支持同模型对战（标记但不计入ELO）


## 📦 项目结构

```
llm-debate-arena/
├── backend/               # 后端服务 (FastAPI + SQLAlchemy)
│   ├── main.py           # FastAPI 应用入口
│   ├── database.py       # 数据库操作层
│   ├── models.py         # Pydantic 数据模型
│   ├── tournament.py     # 锦标赛编排逻辑
│   ├── judge.py          # 多裁判评分系统
│   ├── elo.py            # ELO 排位算法
│   ├── llm_client.py     # LLM 流式客户端
│   ├── tools.py          # 工具集成 (Python/搜索/计算器)
│   ├── auth.py           # JWT 用户认证
│   ├── utils.py          # 工具函数
│   └── requirements.txt  # Python 依赖
│
├── frontend/              # 前端应用 (React 18 + TypeScript + Vite)
│   ├── src/
│   │   ├── main.tsx      # 应用入口
│   │   ├── App.tsx       # 根组件 (路由配置)
│   │   ├── config.ts     # 环境配置 (API URL 管理)
│   │   ├── index.css     # 全局样式
│   │   ├── pages/        # 页面组件
│   │   │   ├── Arena.tsx          # 辩论竞技场主页
│   │   │   ├── Leaderboard.tsx    # ELO 排行榜
│   │   │   ├── MatchHistory.tsx   # 历史记录
│   │   │   ├── Login.tsx          # 登录页
│   │   │   └── Register.tsx       # 注册页
│   │   ├── components/   # 可复用组件
│   │   │   ├── DebateViewer.tsx   # 辩论流式展示组件
│   │   │   └── Toast.tsx          # 消息提示组件
│   │   └── hooks/        # 自定义 Hooks
│   │       ├── useSSE.ts          # SSE 流式通信 Hook
│   │       └── useToast.ts        # Toast 提示 Hook
│   ├── .env              # 环境变量配置
│   ├── .env.example      # 环境变量模板
│   ├── package.json      # Node 依赖
│   ├── tsconfig.json     # TypeScript 配置
│   ├── vite.config.ts    # Vite 构建配置
│   ├── tailwind.config.js # Tailwind CSS 配置
│   └── postcss.config.js  # PostCSS 配置
│
├── docs/                  # 文档目录
│   ├── DOCKER.md         # Docker 部署指南
│   └── main.png          # 演示截图
├── tests/                 # 测试
├── Dockerfile             # Docker 构建文件
├── docker-compose.yml     # Docker Compose 配置
├── .env.example           # 环境变量模板
├── start.sh               # 本地一键启动脚本
├── pyproject.toml         # Python 项目配置
└── README.md              # 项目说明

详细文档：
- [Docker 部署指南](docs/DOCKER.md)
- [后端 README](backend/README.md)
- [前端 README](frontend/README.md)
```

## 🔜 路线图

- [x] ~~Docker 容器化部署~~
- [x] ~~环境变量配置模型列表~~
- [x] ~~前端支持 Markdown 表格渲染~~
- [x] ~~工具调用按需启用（防止幻觉）~~
- [x] ~~历史记录默认隐藏~~
- [ ] LLM辩论性格可定制
- [ ] 人机对战辩论
- [ ] 赛后复盘报告
- [ ] 观众投票功能
- [ ] 每日挑战赛
- [ ] 社区讨论区


## 📚 文档

- [生产环境部署指南](docs/DEPLOYMENT.md) - HTTPS 部署、Nginx 配置、故障排查
- [前端开发文档](frontend/README.md) - 前端技术栈、开发规范
- [API 文档](http://localhost:8000/docs) - FastAPI 自动生成的 API 文档


## Contact

- Issue(建议)：[![GitHub issues](https://img.shields.io/github/issues/shibing624/llm-debate-arena.svg)](https://github.com/shibing624/llm-debate-arena/issues)
- 邮件我：xuming: xuming624@qq.com
- 微信我：加我*微信号：xuming624, 备注：姓名-公司-NLP* 进NLP交流群。

<img src="docs/wechat.jpeg" width="200" />


## Citation

如果你在研究中使用了`llm-debate-arena`，请按如下格式引用：

APA:
```latex
Xu, M. llm-debate-arena: A debate arena for LLM(Version 1.1.2) [Computer software]. https://github.com/shibing624/llm-debate-arena
```

BibTeX:
```latex
@misc{llm-debate-arena,
  author = {Ming Xu},
  title = {llm-debate-arena: A debate arena for LLM},
  year = {2025},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/shibing624/llm-debate-arena}},
}
```

## License


授权协议为 [The Apache License 2.0](LICENSE)，可免费用做商业用途。请在产品说明中附加llm-debate-arena的链接和授权协议。


## Contribute
项目代码还很粗糙，如果大家对代码有所改进，欢迎提交回本项目，在提交之前，注意以下两点：

 - 在`tests`添加相应的单元测试
 - 使用`python -m pytest -v`来运行所有单元测试，确保所有单测都是通过的

之后即可提交PR。

## References
- [karpathy/llm_council](https://github.com/karpathy/llm-council) - 裁判模块受此项目启发
