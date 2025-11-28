# MT5 Python API インストールガイド

## 現在の状況

- ✅ MetaTrader 5はインストールされています（`C:\Program Files\MetaTrader 5`）
- ✅ MT5は起動しています
- ❌ MT5のPython APIが見つかりません

## インストール方法

### 方法1: pipでインストール（推奨）

PowerShellまたはコマンドプロンプトで以下を実行:

```powershell
python -m pip install MetaTrader5
```

**注意**: パッケージ名が大文字小文字を区別する場合があります。以下のバリエーションも試してください:

```powershell
python -m pip install meta-trader5
python -m pip install metatrader5
```

### 方法2: MT5公式サイトからダウンロード

1. MetaTrader 5の公式サイトにアクセス
2. Python APIパッケージをダウンロード
3. インストール手順に従う

### 方法3: MT5のインストールディレクトリから利用

MT5のインストールディレクトリにPython APIが含まれている場合があります:

1. `C:\Program Files\MetaTrader 5\MQL5\Libraries\Python` を確認
2. そこに `MetaTrader5` フォルダがあるか確認
3. ある場合は、Pythonのパスに追加

### 方法4: MT5を再起動

MT5を起動している状態で、Python APIが利用できる場合があります:

1. MT5を完全に終了
2. MT5を再起動
3. アカウントにログイン
4. 再度 `python test_mt5_connection.py` を実行

## 確認方法

インストール後、以下のコマンドで確認:

```powershell
python test_mt5_connection.py
```

または:

```powershell
python -c "import MetaTrader5 as mt5; print('OK')"
```

## トラブルシューティング

### pipでインストールできない場合

1. Pythonのバージョンを確認: `python --version` (3.7以上が必要)
2. pipをアップグレード: `python -m pip install --upgrade pip`
3. インターネット接続を確認
4. ファイアウォールやプロキシの設定を確認

### MT5に接続できない場合

1. MT5が起動しているか確認
2. MT5にアカウントでログインしているか確認
3. MT5のインストールパスが正しいか確認

## 次のステップ

MT5のPython APIがインストールできたら:

```powershell
python main.py
```

でプログラムを実行できます。



















