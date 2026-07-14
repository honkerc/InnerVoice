# 与神对话 - 部署说明

## 目录结构

```
与神对话/
├── backend/          # Python FastAPI 后端（端口 8001）
├── frontend-vue/     # Vue 3 前端
├── deploy/           # 部署配置
│   ├── nginx.conf    # Nginx 配置
│   └── README.md     # 本文件
└── package.json      # 根项目脚本
```

## 快速启动（开发）

```bash
# 1. 启动后端（端口 8001）
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8001

# 2. 启动前端 dev server（端口 3000，自动代理 /api 到 8001）
cd frontend-vue
npm run dev
```

## 生产部署

### 1. 构建前端

```bash
cd frontend-vue
npm run build
# 产物在 frontend-vue/dist/
```

### 2. 配置 Nginx

- 复制 `deploy/nginx.conf` 到 `/etc/nginx/sites-available/yushenduihua`
- 修改 `server_name` 和 `root` 路径
- 软链到 `sites-enabled`：`ln -s /etc/nginx/sites-available/yushenduihua /etc/nginx/sites-enabled/`
- 测试配置：`nginx -t`
- 重载：`systemctl reload nginx`

### 3. 启动后端（生产）

```bash
cd backend
# 方式一：直接运行
python -m uvicorn main:app --host 127.0.0.1 --port 8001

# 方式二：使用 systemd（推荐）
# 创建 /etc/systemd/system/yushenduihua.service
```

### 4. 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AI_API_KEY` | AI API Key（可选，也可在 settings 页面设置） | 空 |
| `VITE_API_ORIGIN` | 前端直连后端地址（上传/SSE） | `http://127.0.0.1:8001` |

### 5. 默认账户

首次启动自动创建默认用户：
- 用户名：`admin`
- 密码：`admin123`
