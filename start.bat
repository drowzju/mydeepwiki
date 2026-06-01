@echo off
chcp 65001 >nul
REM DeepWiki 启动脚本 (Windows)

echo ==========================================
echo    DeepWiki 启动脚本
echo ==========================================
echo.

REM 检查 .env 文件
if not exist .env (
    echo [警告] 未找到 .env 文件，将使用 .env.example 作为模板
    copy .env.example .env >nul 2>&1
    echo [提示] 请编辑 .env 文件，填入至少一个 LLM 提供商的 API 密钥
    echo.
)

REM 安装前端依赖
echo [1/4] 检查前端依赖...
if not exist node_modules (
    echo         正在安装前端依赖 (yarn install)...
    call yarn install
    if errorlevel 1 (
        echo [错误] 前端依赖安装失败
        exit /b 1
    )
) else (
    echo         前端依赖已安装
)

REM 安装后端依赖
echo [2/4] 检查后端依赖...
cd api
REM 检查 Poetry 是否安装
poetry --version >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装 Poetry...
    pip install poetry==2.0.1
)

REM 检查虚拟环境
poetry run python --version >nul 2>&1
if errorlevel 1 (
    echo         正在安装后端依赖 (poetry install)...
    poetry install --no-interaction
    if errorlevel 1 (
        echo [错误] 后端依赖安装失败
        cd ..
        exit /b 1
    )
) else (
    echo         后端依赖已安装
)
cd ..

REM 构建前端
echo [3/4] 构建前端...
call yarn build
if errorlevel 1 (
    echo [错误] 前端构建失败
    exit /b 1
)

REM 启动应用
echo [4/4] 启动应用...
echo.
echo ==========================================
echo    启动完成！
echo    前端: http://localhost:3000
echo    后端: http://localhost:8001
echo ==========================================
echo.
echo [提示] 按 Ctrl+C 停止服务
echo.

REM 使用 PowerShell 同时启动两个服务
powershell -Command "
    $backend = Start-Process -NoNewWindow -PassThru -FilePath 'poetry' -ArgumentList 'run','python','-m','api.main' -WorkingDirectory 'api'
    $frontend = Start-Process -NoNewWindow -PassThru -FilePath 'yarn' -ArgumentList 'start'

    Write-Host '服务已启动，按 Ctrl+C 停止...' -ForegroundColor Green

    try {
        while ($true) {
            Start-Sleep -Seconds 1
        }
    } finally {
        Write-Host '正在停止服务...' -ForegroundColor Yellow
        Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
        Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
    }
"
