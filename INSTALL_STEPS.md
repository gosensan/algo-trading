# MT5 Python API インストール手順

## 現在の状況

- ✅ MT5はインストールされています
- ✅ MT5は起動しています
- ✅ アカウントにログインしています
- ❌ Python APIが見つかりません

## インストール手順

### ステップ1: MT5公式サイトからPython APIをダウンロード

1. 以下のURLにアクセス:
   ```
   https://www.mql5.com/ja/docs/integration/python_metatrader5
   ```

2. Python APIパッケージをダウンロード
   - 通常は `.zip` ファイルとして提供されています

### ステップ2: ダウンロードしたファイルを解凍

1. ダウンロードした `.zip` ファイルを解凍
2. `MetaTrader5` フォルダが含まれていることを確認

### ステップ3: Pythonのsite-packagesにコピー

1. 解凍した `MetaTrader5` フォルダを以下の場所にコピー:
   ```
   C:\Users\owner\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\MetaTrader5
   ```

2. または、このプロジェクトのディレクトリに `MetaTrader5` フォルダを配置

### ステップ4: インストールの確認

以下のコマンドで確認:

```powershell
python test_mt5_connection.py
```

または:

```powershell
python -c "import MetaTrader5 as mt5; print('OK')"
```

## 代替方法: プロジェクトディレクトリに配置

Pythonのsite-packagesにコピーする代わりに、このプロジェクトのディレクトリに `MetaTrader5` フォルダを配置することもできます。

1. ダウンロードした `MetaTrader5` フォルダを、このプロジェクトのルートディレクトリにコピー
2. プログラムを実行

## トラブルシューティング

### Python APIが見つからない場合

1. `MetaTrader5` フォルダが正しい場所にコピーされているか確認
2. Pythonのバージョンが3.7以上であることを確認
3. MT5が起動していることを確認

### 接続エラーが発生する場合

1. MT5が起動していることを確認
2. MT5にアカウントでログインしていることを確認
3. MT5のインストールパスが正しいか確認

## 次のステップ

Python APIのインストールが完了したら:

```powershell
python main.py
```

でプログラムを実行できます。



















