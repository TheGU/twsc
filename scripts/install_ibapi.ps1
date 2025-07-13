# Install latest ibapi from Interactive Brokers source
# This script downloads and installs the same version used in CI/CD for Windows

Write-Host "🔄 Installing latest ibapi from Interactive Brokers source..." -ForegroundColor Cyan

# Download URL for Windows
$DownloadUrl = "https://interactivebrokers.github.io/downloads/twsapi_windows.1030.01.msi"
$ArchiveName = "twsapi_windows.1030.01.msi"

try {
    Write-Host "📥 Downloading TWS API package..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $ArchiveName -UseBasicParsing
    
    Write-Host "⚠️  Manual installation required for Windows MSI package" -ForegroundColor Yellow
    Write-Host "Please run the downloaded MSI file: $ArchiveName" -ForegroundColor Yellow
    Write-Host "After installation, navigate to the installation directory and run:" -ForegroundColor Yellow
    Write-Host "  cd 'C:\TWS API\source\pythonclient'" -ForegroundColor White
    Write-Host "  python setup.py install" -ForegroundColor White
    
    Write-Host "🎉 Download complete! Please complete manual installation steps above." -ForegroundColor Green
}
catch {
    Write-Host "❌ Error downloading TWS API: $_" -ForegroundColor Red
    exit 1
}
