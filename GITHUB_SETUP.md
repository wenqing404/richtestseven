# GitHub 设置指南

由于环境限制，我们无法直接创建GitHub仓库并推送代码。以下是手动设置的步骤：

## 1. 创建GitHub仓库

1. 登录您的GitHub账户
2. 点击右上角的"+"图标，选择"New repository"
3. 仓库名称设置为：`Financial_Platform`
4. 添加描述：`基于FastAPI的财报数据爬取与分析平台`
5. 选择"Public"（公开）
6. 不要初始化仓库（不要添加README、.gitignore或许可证）
7. 点击"Create repository"

## 2. 推送代码到GitHub

在您的本地计算机上，克隆此项目后，执行以下命令：

```bash
# 进入项目目录
cd Financial_Platform

# 设置远程仓库URL（替换YOUR_USERNAME为您的GitHub用户名）
git remote add origin https://github.com/YOUR_USERNAME/Financial_Platform.git

# 推送代码到GitHub
git push -u origin main
```

## 3. 项目结构

```
Financial_Platform/
├── app/
│   ├── models/
│   │   └── crawler_models.py
│   ├── routers/
│   │   ├── analysis.py
│   │   ├── crawler.py
│   │   └── llm_analysis.py
│   └── services/
│       ├── analysis_service.py
│       ├── crawler_service.py
│       └── llm_analysis_service.py
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/
│   ├── analysis.html
│   ├── base.html
│   ├── crawler.html
│   ├── index.html
│   └── llm_analysis.html
├── .gitignore
├── Dockerfile
├── README.md
├── main.py
├── requirements.txt
└── run.sh
```

## 4. 配置说明

1. 在生产环境中，请替换`run.sh`中的API密钥：
   ```bash
   export OPENAI_API_KEY="your-actual-api-key"
   ```

2. 如果需要更改端口，可以在`run.sh`中修改：
   ```bash
   export PORT=12001  # 修改为您需要的端口
   ```

## 5. 运行应用

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
./run.sh
```

应用将在http://localhost:12001上运行（或您在run.sh中设置的端口）。