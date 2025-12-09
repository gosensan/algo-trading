# MT5 Python API インストール問題の解決方法

## 問題

```
ERROR: Could not find a version that satisfies the requirement MetaTrader5 (from versions: none)
ERROR: No matching distribution found for MetaTrader5
```

このエラーは、MetaTrader5のPython APIがPyPIに登録されていないため発生します。

## 解決方法

### 方法1: MT5を起動してから実行（最も簡単）

**MetaTrader 5が起動している状態で、Python APIが利用できる場合があります。**

1. **MetaTrader 5を起動**
2. **アカウントにログイン**
3. **このプログラムを実行**:
   ```powershell
   python main.py
   ```

MT5が起動している状態であれば、MT5のDLLが読み込まれ、Python APIが利用できる場合があります。

### 方法2: MT5公式サイトからダウンロード

1. MT5の公式ドキュメントにアクセス:
   - https://www.mql5.com/ja/docs/integration/python_metatrader5

2. Python APIパッケージをダウンロード

3. インストール手順に従う

### 方法3: MT5のインストールディレクトリから直接利用

MT5のインストールディレクトリにPython APIが含まれている場合があります。

1. `C:\Program Files\MetaTrader 5` を確認
2. `MQL5\Libraries\Python` フォルダを確認
3. そこに `MetaTrader5` フォルダがあるか確認
4. ある場合は、Pythonのパスに追加

### 方法4: 手動でパッケージをインストール

MT5の公式サイトからPython APIパッケージをダウンロードし、手動でインストールします。

## 推奨される手順

1. **まず、方法1を試してください**（MT5を起動してから実行）
   - これが最も簡単で確実な方法です

2. 方法1で動作しない場合、方法2を試してください
   - MT5の公式サイトからPython APIをダウンロード

3. それでも解決しない場合、MT5のサポートに問い合わせてください

## 確認方法

MT5のPython APIが正しくインストールされているか確認:

```powershell
python test_mt5_connection.py
```

または:

```powershell
python -c "import MetaTrader5 as mt5; print('OK')"
```

## 現在の状況

- ✅ MT5はインストールされています（`C:\Program Files\MetaTrader 5`）
- ✅ MT5は起動しています（terminal64プロセスを確認）
- ❌ Python APIパッケージが見つかりません

**次のステップ**: MT5が起動している状態で、`python main.py` を実行してみてください。



















