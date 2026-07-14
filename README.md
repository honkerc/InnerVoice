# 与神对话

项目按模块分目录：

```
与神对话/
├── backend/         # FastAPI 后端（含 data、uploads、scripts）
├── frontend-vue/    # Vue 3 前端（全新重写，Vite + Vue Router）
└── frontend-next/   # Next.js 旧版前端（归档）
```

## 启动

需要两个终端。

### 1. 后端（端口 8000）

在项目根目录：

```bash
npm run backend
```

或：

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 2. 前端 Vue（端口 3000）

在项目根目录：

```bash
npm run dev
```

或进入 `frontend-vue/`：

```bash
cd frontend-vue
npm install
npm run dev
```

浏览器打开：**http://localhost:3000**

### AI API Key

可在设置页输入 API Key，**仅保存到服务端**，浏览器不会读取或缓存 Key 值（留空则不修改已有 Key）。也可通过环境变量配置：

```bash
# Windows PowerShell
$env:AI_API_KEY="sk-..."
npm run backend
```

环境变量优先级高于数据库中的 Key。Ollama 本地模式无需配置。

### 旧版 Next.js 前端（可选）

```bash
npm run dev:next
```

或：

```bash
cd frontend-next
npm install
npm run dev
```

---

## 构建

```bash
npm run build:vue    # Vue 生产构建 → frontend-vue/dist/
npm run build:next   # Next 生产构建 → frontend-next/.next/
```

---

## 模拟数据（可选）

```bash
cd backend
python seed_demo.py --replace
```

---

## 工具脚本

开发用脚本在 `backend/scripts/`，数据输出到 `backend/data/`。
