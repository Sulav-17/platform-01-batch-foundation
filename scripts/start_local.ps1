$ErrorActionPreference = "Stop"

Write-Host "Starting Ontario Energy Warehouse..."

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

docker compose up -d

if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose failed to start."
}

Write-Host "Waiting for PostgreSQL..."

$databaseReady = $false

for ($attempt = 1; $attempt -le 30; $attempt++) {
    docker compose exec -T postgres `
        pg_isready `
        -U energy_user `
        -d ontario_energy *> $null

    if ($LASTEXITCODE -eq 0) {
        $databaseReady = $true
        break
    }

    Start-Sleep -Seconds 1
}

if (-not $databaseReady) {
    throw "PostgreSQL did not become ready within 30 seconds."
}

Write-Host "Applying database schema..."

Get-Content sql/schema.sql -Raw |
    docker compose exec -T postgres `
        psql `
        -U energy_user `
        -d ontario_energy

if ($LASTEXITCODE -ne 0) {
    throw "Database schema setup failed."
}

Write-Host ""
Write-Host "Local warehouse is ready."
Write-Host "PostgreSQL: localhost:5433"
Write-Host "Database: ontario_energy"
