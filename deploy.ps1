# ═══════════════════════════════════════════
# FraudLens — One-Click Deployment (Windows)
# ═══════════════════════════════════════════

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FraudLens Deployment Script v2.0"     -ForegroundColor Cyan
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
    if ($retryCount % 5 -eq 0) {
        Write-Host "  Still waiting... ($retryCount/$maxRetries)" -ForegroundColor DarkYellow
    }
}
if ($retryCount -ge $maxRetries) {
    Write-Host "  ERROR: Docker Engine did not start in time. Please start Docker Desktop manually." -ForegroundColor Red
    exit 1
}

# ── Step 2: Clean slate ──
Write-Host "[3/6] Cleaning up old containers..." -ForegroundColor Yellow
docker-compose down --remove-orphans 2>&1 | Out-Null

# ── Step 3: Build and launch ──
Write-Host "[4/6] Building and launching containers..." -ForegroundColor Yellow
docker-compose up -d --build
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

# Give Neo4j a bit more time
Start-Sleep -Seconds 5

# ── Step 5: Seed data ──
Write-Host "[6/6] Seeding database with demo data..." -ForegroundColor Yellow
docker-compose exec -T backend python scripts/seed_test_data.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Data seeded successfully!" -ForegroundColor Green
} else {
    Write-Host "  Warning: Seed script had errors (data may already exist, which is OK)." -ForegroundColor DarkYellow
}

# ── Done ──
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Dashboard:    http://localhost:3000" -ForegroundColor Cyan
Write-Host "  API Docs:     http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Neo4j Browser: http://localhost:7474" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Login:  investigator@fraudlens.gov / fraudlens2026" -ForegroundColor White
Write-Host ""
