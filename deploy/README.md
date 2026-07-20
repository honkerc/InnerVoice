# InnerVoice - 部署说明

## 目录结构

```
InnerVoice/
├── backend/              # Python FastAPI 后端
├── frontend-vue/         # Vue 3 前端
├── deploy/               # 部署配置
│   ├── nginx.conf        # Nginx 反向代理配置
│   ├── innervoice.service # systemd 服务文件
│   ├── start.sh          # 一键启动脚本
│   └── README.md         # 本文件
└── package.json          # 根项目脚本
```

## 快速启动（开发）

```bash
# 1. 启动后端（默认端口 8001）
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

- 复制 `deploy/nginx.conf` 到 `/etc/nginx/sites-available/innervoice`
- 修改 `server_name` 和 `root` 路径
- 软链：`ln -s /etc/nginx/sites-available/innervoice /etc/nginx/sites-enabled/`
- 测试：`nginx -t`
- 重载：`systemctl reload nginx`

### 3. 启动后端

#### 方式一：一键脚本

```bash
# 默认端口 8001
bash deploy/start.sh

# 自定义端口
INNERVOICE_PORT=8080 bash deploy/start.sh

# 自定义数据目录
INNERVOICE_DATA_DIR=/var/lib/innervoice/data bash deploy/start.sh
```

#### 方式二：systemd 服务（推荐）

```bash
# 1. 配置真实值：cp backend/.env.example backend/.env 并填好
#    （AI_API_KEY、INNERVOICE_DATA_DIR 等都在这里，不要写进 service 文件）
# 2. 修改 deploy/innervoice.service 中的 User/Group/WorkingDirectory/--port
# 3. 复制到系统目录
sudo cp deploy/innervoice.service /etc/systemd/system/

# 4. 重载并启动
sudo systemctl daemon-reload
sudo systemctl enable innervoice
sudo systemctl start innervoice

# 5. 查看状态
sudo systemctl status innervoice
```

### 4. 环境变量

统一写在 `backend/.env`（从 `.env.example` 复制），config.py 启动时自动加载，不需要在 systemd 单元里重复配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `INNERVOICE_PORT` | 供应用内部读取；实际监听端口以 service 文件里的 `--port` 为准，两处保持一致（当前部署为 `8000`） | `8001` |
| `INNERVOICE_DATA_DIR` | 数据目录（数据库、上传文件） | `backend/data/` |
| `AI_API_KEY` | AI API Key（可选，也可在 settings 页面设置；留空/不填此项时以 settings 页面为准） | 空 |
| `VITE_API_ORIGIN` | 前端直连后端地址（上传/SSE） | `http://127.0.0.1:8001` |

> 修改端口后需同步修改 service 文件里的 `--port` 和 Nginx 配置中的 `proxy_pass` 地址。

### 5. 默认账户

首次启动自动创建默认用户：
- 用户名：`admin`
- 密码：`admin123`
