[CmdletBinding()]
param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [string]$LanIp = "",
    [switch]$SkipInstall,
    [switch]$NoBrowser,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$Root = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
$BackendProcess = $null
$FrontendProcess = $null

function Write-Step {
    param([string]$Message)
    Write-Host "[课堂签到] $Message" -ForegroundColor Cyan
}

function Fail {
    param([string]$Message)
    Write-Host "[课堂签到] $Message" -ForegroundColor Red
    exit 1
}

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Find-Python {
    $candidates = @(
        @{ Exe = "py"; Args = @("-3.12") },
        @{ Exe = "py"; Args = @("-3.11") },
        @{ Exe = "py"; Args = @("-3.13") },
        @{ Exe = "py"; Args = @("-3") },
        @{ Exe = "python"; Args = @() }
    )

    foreach ($candidate in $candidates) {
        if (-not (Get-Command $candidate.Exe -ErrorAction SilentlyContinue)) {
            continue
        }
        $probe = & $candidate.Exe @($candidate.Args + @("-c", "print('OK')")) 2>$null
        if ($LASTEXITCODE -eq 0 -and (($probe -join "`n") -match "OK")) {
            return $candidate
        }
    }
    return $null
}

function Invoke-ProjectPython {
    param([string[]]$Arguments)
    & $script:PythonExe @($script:PythonBaseArgs + $Arguments)
}

function Ensure-PythonVenv {
    param(
        [string]$Component,
        [string]$Requirements
    )

    $venvPath = Join-Path $Root "$Component\.venv-win"
    $venvPython = Join-Path $venvPath "Scripts\python.exe"

    if (-not (Test-Path $venvPython)) {
        Write-Step "创建 $Component 的 Windows 虚拟环境..."
        & $script:PythonExe @($script:PythonBaseArgs + @("-m", "venv", $venvPath))
        if ($LASTEXITCODE -ne 0) {
            Fail "创建 $Component 虚拟环境失败。"
        }
    }

    if (-not $SkipInstall) {
        Write-Step "安装 $Component 依赖..."
        & $venvPython -m pip install --upgrade pip --disable-pip-version-check --quiet
        & $venvPython -m pip install -r (Join-Path $Root $Requirements) --disable-pip-version-check --quiet
        if ($LASTEXITCODE -ne 0) {
            Fail "$Component 依赖安装失败。"
        }
    }

    return $venvPython
}

function Test-LanIp {
    param([string]$Ip)
    return $Ip -match '^\d{1,3}(\.\d{1,3}){3}$'
}

function Get-LanIp {
    $configs = @(Get-NetIPConfiguration | Where-Object {
        $_.IPv4DefaultGateway -and
        $_.NetAdapter.Status -eq "Up" -and
        $_.InterfaceAlias -notmatch "vEthernet|WSL|Loopback|Tailscale"
    })

    $preferred = $configs |
        Where-Object { $_.InterfaceAlias -match "WLAN|Wi-Fi|Ethernet|以太网|无线" } |
        Select-Object -First 1

    if (-not $preferred) {
        $preferred = $configs | Select-Object -First 1
    }
    if ($preferred) {
        $addresses = @($preferred.IPv4Address.IPAddress)
        if ($addresses.Count -gt 0) {
            return $addresses[0]
        }
    }
    return "127.0.0.1"
}

function Wait-Http {
    param(
        [string]$Url,
        [int]$Seconds
    )

    for ($i = 0; $i -lt $Seconds; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                return $true
            }
        } catch {
            # 服务尚未就绪
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Assert-PortFree {
    param([int]$Port)
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        Fail "端口 $Port 已被占用，请先停止占用进程。"
    }
}

function Stop-ProcessTree {
    param($Process)
    if ($Process -and -not $Process.HasExited) {
        & taskkill.exe /PID $Process.Id /T /F 2>$null | Out-Null
    }
}

if ($Root -match '^\\\\') {
    Fail "当前项目位于网络路径：$Root。纯 Windows 启动要求项目在本地磁盘，请先复制/克隆到 C:\teachers-treasure 再运行。"
}

if (-not (Test-Path (Join-Path $Root "backend\app\main.py"))) {
    Fail "未找到 backend\app\main.py，请在项目根目录运行此脚本。"
}

$script:PythonInfo = Find-Python
if (-not $script:PythonInfo) {
    Fail "未检测到 Python。请安装 Python 3.12：winget install Python.Python.3.12"
}
$script:PythonExe = $script:PythonInfo.Exe
$script:PythonBaseArgs = $script:PythonInfo.Args

$pythonVersion = Invoke-ProjectPython @(
    "-c",
    "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
)
if ($LASTEXITCODE -ne 0) {
    Fail "Python 无法运行。"
}
$parts = ($pythonVersion | Select-Object -First 1).Trim().Split(".")
if ([int]$parts[0] -lt 3 -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -lt 11)) {
    Fail "需要 Python 3.11 及以上，推荐 3.12。当前：$pythonVersion"
}

$node = Get-Command node.exe -ErrorAction SilentlyContinue
$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $node -or -not $npm) {
    Fail "未检测到 Node.js。请安装 LTS：winget install OpenJS.NodeJS.LTS"
}
$NodeExe = $node.Source
$NpmCmd = $npm.Source

if (-not (Test-LanIp $LanIp)) {
    $LanIp = Get-LanIp
}

if ($DryRun) {
    Write-Host "项目目录：$Root"
    Write-Host "Python：$($script:PythonInfo.Exe) $($script:PythonInfo.Args -join ' ') ($pythonVersion)"
    Write-Host "Node：$(& $NodeExe --version)"
    Write-Host "本机访问：http://localhost:$FrontendPort"
    Write-Host "手机访问：http://${LanIp}:$FrontendPort"
    exit 0
}

$databasePython = Ensure-PythonVenv "database" "database\requirements.txt"
$backendPython = Ensure-PythonVenv "backend" "backend\requirements.txt"

if (-not (Test-Path (Join-Path $Root "frontend\node_modules\.bin\vite.cmd"))) {
    if ($SkipInstall) {
        Fail "前端依赖未安装，请先执行 npm install。"
    }
    Write-Step "安装前端依赖..."
    Push-Location (Join-Path $Root "frontend")
    & $NpmCmd install --package-lock=false --registry=https://registry.npmjs.org
    $npmExit = $LASTEXITCODE
    Pop-Location
    if ($npmExit -ne 0) {
        Fail "前端依赖安装失败。"
    }
}

$databasePath = Join-Path $Root "database\teacher_treasure.db"
$env:DATABASE_URL = "sqlite:///$($databasePath -replace '\\', '/')"
$env:JWT_SECRET = if ($env:JWT_SECRET) { $env:JWT_SECRET } else { "dev-only-insecure-jwt-secret-change-before-production" }
$env:SEED_TEACHER_PASSWORD = if ($env:SEED_TEACHER_PASSWORD) { $env:SEED_TEACHER_PASSWORD } else { "Teacher@123" }
$env:PYTHONPATH = $Root
$env:CORS_ORIGINS = "http://localhost:$FrontendPort,http://127.0.0.1:$FrontendPort,http://${LanIp}:$FrontendPort"

Write-Step "初始化数据库..."
& $databasePython -m alembic -c (Join-Path $Root "database\alembic.ini") upgrade head
if ($LASTEXITCODE -ne 0) {
    Fail "数据库迁移失败。"
}
& $databasePython -m database.seeds.seed_teacher
if ($LASTEXITCODE -ne 0) {
    Fail "教师种子创建失败。"
}
& $databasePython -m database.seeds.seed_demo
if ($LASTEXITCODE -ne 0) {
    Fail "演示学生种子创建失败。"
}

if (Test-Administrator) {
    Write-Step "配置 Windows 防火墙..."
    foreach ($port in @($FrontendPort, $BackendPort)) {
        $ruleName = "TeacherTreasure-$port"
        if (-not (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
            New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort $port -Action Allow -Profile Any | Out-Null
        }
    }
} else {
    Write-Host "[提示] 手机打不开时，请右键以管理员身份运行一次本脚本，放行 5173/8000 防火墙。" -ForegroundColor Yellow
}

Assert-PortFree $BackendPort
Assert-PortFree $FrontendPort

$backendLog = Join-Path $Root "backend\uvicorn.log"
$backendErrorLog = Join-Path $Root "backend\uvicorn.err.log"
$frontendLog = Join-Path $Root "frontend\vite.log"
$frontendErrorLog = Join-Path $Root "frontend\vite.err.log"

$env:VITE_USE_MOCK = "false"
$env:VITE_API_BASE_URL = ""

try {
    Write-Step "启动后端..."
    $BackendProcess = Start-Process -FilePath $backendPython `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "$BackendPort") `
        -WorkingDirectory (Join-Path $Root "backend") `
        -RedirectStandardOutput $backendLog `
        -RedirectStandardError $backendErrorLog `
        -WindowStyle Hidden `
        -PassThru

    if (-not (Wait-Http "http://127.0.0.1:$BackendPort/api/v1/health" 40)) {
        Get-Content $backendErrorLog -ErrorAction SilentlyContinue | Select-Object -Last 30
        Fail "后端启动失败，日志：$backendErrorLog"
    }

    Write-Step "启动前端..."
    $FrontendProcess = Start-Process -FilePath $NpmCmd `
        -ArgumentList @("run", "dev", "--", "--host", "0.0.0.0", "--port", "$FrontendPort") `
        -WorkingDirectory (Join-Path $Root "frontend") `
        -RedirectStandardOutput $frontendLog `
        -RedirectStandardError $frontendErrorLog `
        -WindowStyle Hidden `
        -PassThru

    if (-not (Wait-Http "http://127.0.0.1:$FrontendPort" 60)) {
        Get-Content $frontendErrorLog -ErrorAction SilentlyContinue | Select-Object -Last 30
        Fail "前端启动失败，日志：$frontendErrorLog"
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  课堂签到已启动（纯 Windows）" -ForegroundColor Green
    Write-Host "----------------------------------------"
    Write-Host "  本机访问:   http://localhost:$FrontendPort"
    Write-Host "  手机访问:   http://${LanIp}:$FrontendPort"
    Write-Host "  后端 API:   http://${LanIp}:$BackendPort"
    Write-Host ""
    Write-Host "  教师账号:   teacher / Teacher@123"
    Write-Host "  学生账号:   20230001 / 20230001（首次登录需改密）"
    Write-Host "             20230002 / 20230002"
    Write-Host "  班长账号:   20230003 / 20230003"
    Write-Host ""
    Write-Host "  手机需与电脑同一 Wi-Fi。"
    Write-Host "  按 Enter 停止前后端。"
    Write-Host "========================================" -ForegroundColor Green

    if (-not $NoBrowser) {
        Start-Process "http://localhost:$FrontendPort" | Out-Null
    }

    [void][Console]::ReadLine()
} finally {
    Write-Step "正在停止前后端..."
    Stop-ProcessTree $FrontendProcess
    Stop-ProcessTree $BackendProcess
}