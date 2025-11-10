# Vosk Model Setup Script for JARVIS
# This script downloads and installs the Vosk speech recognition model

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Vosk Model Setup for JARVIS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to project directory
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDir

# Create models directory if it doesn't exist
if (-not (Test-Path "models")) {
    New-Item -ItemType Directory -Path "models" | Out-Null
    Write-Host "✓ Created 'models' directory" -ForegroundColor Green
} else {
    Write-Host "✓ 'models' directory already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "Choose a Vosk model to download:" -ForegroundColor Yellow
Write-Host "1. Small model (40 MB) - Recommended for most users" -ForegroundColor White
Write-Host "2. Standard model (1.8 GB) - Better accuracy, larger size" -ForegroundColor White
Write-Host "3. Large model (2.3 GB) - Best accuracy" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-3) [Default: 1]"

if ([string]::IsNullOrWhiteSpace($choice)) {
    $choice = "1"
}

switch ($choice) {
    "1" {
        $modelName = "vosk-model-small-en-us-0.15"
        $modelUrl = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        $modelSize = "40 MB"
    }
    "2" {
        $modelName = "vosk-model-en-us-0.22"
        $modelUrl = "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"
        $modelSize = "1.8 GB"
    }
    "3" {
        $modelName = "vosk-model-en-us-0.42-gigaspeech"
        $modelUrl = "https://alphacephei.com/vosk/models/vosk-model-en-us-0.42-gigaspeech.zip"
        $modelSize = "2.3 GB"
    }
    default {
        Write-Host "Invalid choice. Using small model (default)." -ForegroundColor Yellow
        $modelName = "vosk-model-small-en-us-0.15"
        $modelUrl = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        $modelSize = "40 MB"
    }
}

$zipPath = "models\$modelName.zip"
$extractPath = "models"

# Check if model already exists
if (Test-Path "models\$modelName") {
    Write-Host ""
    Write-Host "⚠ Model '$modelName' already exists!" -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to re-download? (y/n) [Default: n]"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Host "Skipping download. Using existing model." -ForegroundColor Green
        exit 0
    }
    Remove-Item "models\$modelName" -Recurse -Force
}

Write-Host ""
Write-Host "Downloading $modelName ($modelSize)..." -ForegroundColor Cyan
Write-Host "This may take a few minutes depending on your internet speed." -ForegroundColor Yellow
Write-Host ""

try {
    # Download the model
    Invoke-WebRequest -Uri $modelUrl -OutFile $zipPath -UseBasicParsing
    
    Write-Host "✓ Download complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Extracting model..." -ForegroundColor Cyan
    
    # Extract the ZIP file
    Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force
    
    Write-Host "✓ Extraction complete!" -ForegroundColor Green
    Write-Host ""
    
    # Remove ZIP file
    Remove-Item $zipPath -Force
    Write-Host "✓ Cleaned up ZIP file" -ForegroundColor Green
    Write-Host ""
    
    # Verify installation
    if (Test-Path "models\$modelName") {
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "✓ Vosk model installed successfully!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Model location: models\$modelName" -ForegroundColor White
        Write-Host ""
        Write-Host "You can now restart JARVIS to use offline speech recognition!" -ForegroundColor Cyan
        Write-Host ""
        
        # Test if Vosk can load the model
        Write-Host "Testing model loading..." -ForegroundColor Cyan
        python -c "from vosk import Model; m = Model('models/$modelName'); print('✓ Model loaded successfully!')" 2>&1
    } else {
        Write-Host "⚠ Error: Model folder not found after extraction" -ForegroundColor Red
        Write-Host "Please check the extraction manually." -ForegroundColor Yellow
    }
    
} catch {
    Write-Host ""
    Write-Host "✗ Error occurred: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Manual setup instructions:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://alphacephei.com/vosk/models" -ForegroundColor White
    Write-Host "2. Extract to: models\$modelName" -ForegroundColor White
    Write-Host "3. Restart JARVIS" -ForegroundColor White
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

