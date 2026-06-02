# AI Resume Analysis System

基于 **LangChain + DeepSeek** 的 AI 简历智能解析与评分系统。上传 PDF 简历 + 岗位描述，自动完成简历结构化提取和岗位匹配度评分。

## 📊 系统架构

```
┌──────────────┐     ┌──────────────┐     ┌─────────────────┐
│  GitHub Pages │────▶│  FastAPI 后端 │────▶│  DeepSeek API    │
│  前端  (静态)  │     │  (RESTful)    │     │  (LLM 推理)       │
└──────────────┘     └──────┬───────┘     └─────────────────┘
                            │
                     ┌──────▼───────┐
                     │  Redis 缓存   │
                     │  (MD5 去重)   │
                     └──────────────┘
```

### 核心模块

| 模块 | 文件 | 功能 |
|------|------|------|
| **PDF 解析** | `app/pdf_loader.py` | PyPDFLoader + pdfplumber 双引擎提取 |
| **AI 简历解析** | `app/ai_parser.py` | DeepSeek JSON 模式结构化输出 |
| **岗位评分** | `app/scorer.py` | Prompt 工程：S=0.6×S_skill+0.4×S_exp |
| **缓存层** | `app/cache.py` | Key=MD5(PDF)+MD5(JD)，Redis 优先，内存降级 |
| **API 接口** | `app/main.py` | FastAPI + Tenacity 指数退避重试 |
| **数据模型** | `app/models.py` | Pydantic v2 强约束校验 |

## 🛠 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | **FastAPI** | 原生异步，自动生成 OpenAPI 文档 |
| AI 编排 | **LangChain** | Prompt 管理 + 模型调用链 |
| 推理模型 | **DeepSeek-V3** | 高性价比，function calling 能力 |
| 缓存 | **Redis** | MD5 去重，TTL 7 天，内存降级 |
| 重试 | **Tenacity** | 指数退避，最大 3 次重试 |
| PDF 解析 | **PyPDF + pdfplumber** | 双引擎组合，表格识别 |

## 📁 项目结构

```
resume_analyzer/
├── app/
│   ├── main.py          # FastAPI 入口，路由定义
│   ├── models.py        # Pydantic 数据模型
│   ├── config.py        # 环境变量配置
│   ├── ai_parser.py     # LangChain + DeepSeek 简历解析
│   ├── scorer.py        # 岗位匹配评分
│   ├── pdf_loader.py    # PDF 文本提取
│   └── cache.py         # Redis/内存缓存
├── static/
│   └── index.html       # 前端上传页面
├── docs/                # GitHub Pages 部署文件
├── .env.example         # 环境变量模板
├── requirements.txt     # Python 依赖
├── .gitignore
└── README.md
```

## 🚀 快速开始

### 1. 环境准备

```bash
# Python 3.11+
python --version

# 克隆项目
git clone https://github.com/bitqyh/AI_test.git
cd AI_test
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入 DeepSeek API Key：

```env
DEEPSEEK_API_KEY=sk-your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

> 🔑 获取 API Key：[DeepSeek 开放平台](https://platform.deepseek.com/)

### 4. 启动服务

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### 5. 访问

| 入口 | 地址 |
|------|------|
| 前端界面 | http://localhost:8080 |
| API 文档 (Swagger) | http://localhost:8080/docs |
| 健康检查 | http://localhost:8080/api/v1/system/health |

## 📡 API 接口

### POST `/api/v1/resume/analyze`

上传 PDF 简历并返回解析 + 评分结果。

**请求：** `multipart/form-data`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | File | 是 | PDF 简历文件 |
| `job_description` | String | 否 | 岗位描述文本 |

**响应示例：**

```json
{
  "resume": {
    "basic_info": { "name": "张三", "phone": "13800138000", "email": "zhangsan@example.com" },
    "job_intention": "高级Python后端开发工程师",
    "education": [{ "school": "北京大学", "degree": "硕士", "major": "计算机科学与技术" }],
    "work_experience": [{ "company": "阿里巴巴", "position": "高级Python开发工程师" }],
    "skills": ["Python", "FastAPI", "Docker", "Kubernetes"],
    "projects": [{ "name": "智能客服系统", "role": "技术负责人" }]
  },
  "match": {
    "overall_score": 92.0,
    "skill_score": 95.0,
    "experience_score": 87.5,
    "highlights": "精通FastAPI，有大规模分布式系统经验",
    "gaps": "缺少前端开发经验",
    "recommendation": "技能和经验高度匹配，建议录用"
  },
  "from_cache": false
}
```

### GET `/api/v1/system/health`

健康检查接口，返回服务状态。

## 💾 缓存策略

- **缓存 Key**：`MD5(简历文件内容) + MD5(岗位描述)`
- **命中条件**：同一份简历针对同一岗位重复投递
- **TTL**：7 天（可通过 `CACHE_TTL_DAYS` 配置）
- **降级**：Redis 不可用时自动切换内存缓存

## 🔧 阿里云函数计算 (FC) 部署

本项目设计支持阿里云 Serverless 部署：

```bash
# 安装 Serverless Devs
npm install -g @serverless-devs/s

# 部署
s deploy
```

**冷启动优化已完成：**
- LLM 实例采用懒加载，在函数实例复用时避免重复初始化
- 全局变量的依赖导入放在模块顶层

## 🌐 GitHub Pages 前端

前端静态页面部署于 GitHub Pages，访问地址：

👉 [https://bitqyh.github.io/AI_test/](https://bitqyh.github.io/AI_test/)

> 注意：前端需要后端 API 运行才能完整使用。本地启动后端后，前端默认调用 `localhost:8080` 的 API。

## 📄 License

MIT
