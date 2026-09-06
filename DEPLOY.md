# 公网部署指南

## 推荐方案：Render（免费、稳定、有固定域名）

### 1. 注册 Render 账号
- 访问 https://render.com/
- 用 GitHub 账号一键登录

### 2. 把项目上传到 GitHub
```bash
# 在项目目录下执行
git init
git add .
git commit -m "init"
# 在 GitHub 新建仓库，然后按提示 push
```

### 3. 在 Render 创建 Web Service
- 点击 New → Web Service
- 连接你的 GitHub 仓库
- 配置：
  - Name: expression-pro
  - Region: 选 Singapore（离中国最近）
  - Branch: main
  - Runtime: Python 3
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `gunicorn -b 0.0.0.0:$PORT app:app`
- 点击 Create Web Service

### 4. 初始化数据库
Render 免费实例的文件系统是临时的，重启后 SQLite 数据会丢失。如需持久化，建议：
- 方案 A：升级到 Render Disk（付费）
- 方案 B：每次部署后手动访问一次 `/api/init-db` 初始化（已添加该路由）

### 5. 访问
部署完成后，Render 会分配类似 `https://expression-pro-xxxx.onrender.com` 的域名，手机随时随地都能访问。

---

## 临时方案：ngrok（无需注册、快速公网访问）

如果你只是想临时在手机上测试：

1. 安装 ngrok：https://ngrok.com/download
2. 运行：`ngrok http 5000`
3. 手机访问 ngrok 提供的 `https://xxx.ngrok-free.app` 链接

注意：免费版 ngrok 链接每次重启都会变。
