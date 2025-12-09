# MetaTrader 5 セットアップガイド

## MT5のPython APIをインストールする方法

MetaTrader 5のPython APIを使用するには、以下のいずれかの方法でインストールしてください。

### 方法1: pipでインストール（推奨）

```bash
pip install MetaTrader5
```

または

```bash
python -m pip install MetaTrader5
```

### 方法2: MT5のインストールディレクトリから利用

MT5がインストールされている場合、MT5のインストールディレクトリにPython APIが含まれている場合があります。

1. MT5のインストールディレクトリを確認（通常は `C:\Program Files\MetaTrader 5\` または `C:\Program Files (x86)\MetaTrader 5\`）
2. `MQL5\Libraries\Python` フォルダを確認
3. 必要に応じて、Pythonのパスに追加

### 方法3: 手動インストール

1. [MetaTrader 5公式サイト](https://www.metatrader5.com/)からMT5をダウンロード・インストール
2. MT5を起動してアカウントにログイン
3. Python APIパッケージをインストール

## 動作確認

MT5が正しくインストールされているか確認するには、以下のコマンドを実行してください:

```python
import MetaTrader5 as mt5
print(mt5.initialize())
```

`True` が返されれば、MT5のPython APIが正しくインストールされています。

## トラブルシューティング

### エラー: "MetaTrader5モジュールが見つかりません"

1. MT5がインストールされているか確認
2. MT5が起動しているか確認
3. Pythonのバージョンが3.7以上であることを確認
4. pipでインストールを試す: `pip install MetaTrader5`

### エラー: "MT5初期化エラー"

1. MetaTrader 5が起動しているか確認
2. MT5のインストールパスが正しいか確認
3. MT5にアカウントでログインしているか確認

## 使用方法

1. MetaTrader 5を起動
2. アカウントにログイン
3. このプログラムを実行: `python main.py`

プログラムは自動的にMT5に接続し、ボリンジャーバンド戦略を実行します。



















