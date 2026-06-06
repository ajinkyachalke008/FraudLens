# ═══════════════════════════════════════════
# FraudLens — Native Hybrid Deployment
# ═══════════════════════════════════════════

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FraudLens Native Hybrid Deployment"    -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Start Docker Desktop ──
Write-Host "[1/6] Starting Docker Desktop..." -ForegroundColor Yellow
$dockerDesktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
if (Test-Path $dockerDesktop) {
    Start-Process $dockerDesktop
} else {
    Write-Host "  Docker Desktop not found at default path, assuming it's already running." -ForegroundColor DarkYellow
}

Write-Host "[2/6] Waiting for Docker Engine..." -ForegroundColor Yellow
$maxRetries = 40
$retryCount = 0
while ($retryCount -lt $maxRetries) {
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Docker Engine is ONLINE!" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 3
    $retryCount++
}

# ── Step 2: Clean slate ──
Write-Host "[3/6] Cleaning up old containers..." -ForegroundColor Yellow
docker-compose down --remove-orphans 2>&1 | Out-Null

# ── Step 3: Build and launch DBs ──
Write-Host "[4/6] Booting lightweight databases in Docker..." -ForegroundColor Yellow
docker-compose up -d postgres redis neo4j
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: docker-compose up failed!" -ForegroundColor Red
    exit 1
}

# ── Step 4: Wait for healthy databases ──
Write-Host "[5/6] Waiting for databases to become healthy..." -ForegroundColor Yellow
$waited = 0
$maxWait = 90
while ($waited -lt $maxWait) {
    $pgHealthy = docker inspect --format='{{.State.Health.Status}}' project1-postgres-1 2>$null
    $redisHealthy = docker inspect --format='{{.State.Health.Status}}' project1-redis-1 2>$null
    if ($pgHealthy -eq "healthy" -and $redisHealthy -eq "healthy") {
        Write-Host "  Postgres and Redis are healthy!" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 3
    $waited += 3
}

# ── Step 5: Setup Python Backend Native ──
Write-Host "[6/6] Setting up Native Python Backend & Seeding Data..." -ForegroundColor Yellow
cd backend
if (-Not (Test-Path "venv")) {
    Write-Host "  Creating virtual environment..." -ForegroundColor DarkYellow
    python -m venv venv
}
.\venv\Scripts\activate
Write-Host "  Installing backend dependencies (this may take a few minutes)..." -ForegroundColor DarkYellow
python -m pip install --upgrade pip
pip install torch==2.3.0 torchvision==0.18.0 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# Need to set PYTHONPATH for the seeder
$env:PYTHONPATH = (Get-Location).Path
Write-Host "  Seeding database with demo data..." -ForegroundColor DarkYellow
python scripts\seed_test_data.py

Write-Host "  Starting FastAPI Backend in a new window..." -ForegroundColor DarkYellow
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$((Get-Location).Path)'; .\venv\Scripts\activate; `$env:PYTHONPATH='.'; uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1`""

# ── Step 6: Setup Node.js Frontend Native ──
Write-Host "[7/6] Setting up Native Node.js Frontend..." -ForegroundColor Yellow
cd ..\frontend
Write-Host "  Installing frontend dependencies..." -ForegroundColor DarkYellow
npm install --legacy-peer-deps
Write-Host "  Starting Next.js Frontend in a new window..." -ForegroundColor DarkYellow
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$((Get-Location).Path)'; npm run dev`""
cd ..

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  HYBRID DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Dashboard:    http://localhost:3000" -ForegroundColor Cyan
Write-Host "  API Docs:     http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Neo4j Browser: http://localhost:7474" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Login:  investigator@fraudlens.gov / fraudlens2026" -ForegroundColor White
Write-Host ""
