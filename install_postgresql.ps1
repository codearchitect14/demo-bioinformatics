# PostgreSQL Installation Script for Windows
# This script downloads and installs PostgreSQL 17

Write-Host "Installing PostgreSQL 17..." -ForegroundColor Green

# Create temp directory
$tempDir = "C:\temp\postgresql_install"
if (!(Test-Path $tempDir)) {
    New-Item -ItemType Directory -Path $tempDir -Force
}

# Download PostgreSQL installer
$postgresUrl = "https://get.enterprisedb.com/postgresql/postgresql-17.5-3-windows-x64.exe"
$installerPath = "$tempDir\postgresql-17.5-3-windows-x64.exe"

Write-Host "Downloading PostgreSQL installer..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $postgresUrl -OutFile $installerPath -UseBasicParsing
    Write-Host "Download completed successfully!" -ForegroundColor Green
} catch {
    Write-Host "Download failed. Trying alternative method..." -ForegroundColor Red
    
    # Alternative download method
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($postgresUrl, $installerPath)
    Write-Host "Download completed using alternative method!" -ForegroundColor Green
}

# Install PostgreSQL silently
Write-Host "Installing PostgreSQL..." -ForegroundColor Yellow
$installArgs = @(
    "--unattendedmodeui", "minimal",
    "--mode", "unattended",
    "--superpassword", "Boolmind2025@@",
    "--servicename", "postgresql-x64-17",
    "--serviceaccount", "postgres",
    "--serverport", "5432",
    "--locale", "en_US",
    "--datadir", "C:\Program Files\PostgreSQL\17\data"
)

try {
    Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait
    Write-Host "PostgreSQL installation completed!" -ForegroundColor Green
} catch {
    Write-Host "Installation failed. Please run the installer manually." -ForegroundColor Red
    Write-Host "Installer location: $installerPath" -ForegroundColor Yellow
}

# Add PostgreSQL to PATH
$postgresBinPath = "C:\Program Files\PostgreSQL\17\bin"
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
if ($currentPath -notlike "*$postgresBinPath*") {
    [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$postgresBinPath", "Machine")
    Write-Host "Added PostgreSQL to system PATH" -ForegroundColor Green
}

Write-Host "PostgreSQL installation script completed!" -ForegroundColor Green
Write-Host "Please restart your terminal to use psql commands." -ForegroundColor Yellow 