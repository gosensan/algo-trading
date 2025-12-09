# 環境構築スクリプト
# 仮想環境の作成と依存パッケージのインストールを自動化します

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "環境構築を開始します..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Pythonがインストールされているか確認
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Pythonが見つかりました: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "エラー: Pythonがインストールされていないか、PATHに追加されていません。" -ForegroundColor Red
    Write-Host "Python 3.8以上をインストールしてください。" -ForegroundColor Red
    exit 1
}

# 仮想環境のディレクトリ名
$venvName = "venv"

# 仮想環境が既に存在するか確認
if (Test-Path $venvName) {
    Write-Host "仮想環境 '$venvName' は既に存在します。" -ForegroundColor Yellow
    $response = Read-Host "既存の仮想環境を削除して再作成しますか？ (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host "既存の仮想環境を削除しています..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $venvName
    } else {
        Write-Host "既存の仮想環境を使用します。" -ForegroundColor Green
    }
}

# 仮想環境が存在しない場合、作成
if (-not (Test-Path $venvName)) {
    Write-Host "仮想環境を作成しています..." -ForegroundColor Cyan
    python -m venv $venvName
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "エラー: 仮想環境の作成に失敗しました。" -ForegroundColor Red
        exit 1
    }
    Write-Host "仮想環境が正常に作成されました。" -ForegroundColor Green
}

# 仮想環境を有効化
Write-Host "仮想環境を有効化しています..." -ForegroundColor Cyan
& "$venvName\Scripts\Activate.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "警告: 仮想環境の有効化に失敗しました。手動で有効化してください。" -ForegroundColor Yellow
    Write-Host "コマンド: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
}

# pipをアップグレード
Write-Host "pipをアップグレードしています..." -ForegroundColor Cyan
python -m pip install --upgrade pip

# requirements.txtが存在するか確認
if (Test-Path "requirements.txt") {
    Write-Host "依存パッケージをインストールしています..." -ForegroundColor Cyan
    pip install -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "エラー: 依存パッケージのインストールに失敗しました。" -ForegroundColor Red
        exit 1
    }
    Write-Host "依存パッケージが正常にインストールされました。" -ForegroundColor Green
} else {
    Write-Host "警告: requirements.txtが見つかりません。" -ForegroundColor Yellow
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "環境構築が完了しました！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "仮想環境を有効化するには、以下のコマンドを実行してください:" -ForegroundColor Yellow
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "仮想環境を無効化するには:" -ForegroundColor Yellow
Write-Host "  deactivate" -ForegroundColor White
Write-Host ""



