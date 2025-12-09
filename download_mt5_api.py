"""
MT5 Python API ダウンロードガイド
"""
import os
import sys

print("=" * 60)
print("MT5 Python API インストールガイド")
print("=" * 60)

print("\nMT5のPython APIをインストールするには、以下の手順を実行してください:\n")

print("方法1: MT5公式サイトからダウンロード")
print("-" * 60)
print("1. 以下のURLにアクセス:")
print("   https://www.mql5.com/ja/docs/integration/python_metatrader5")
print("\n2. Python APIパッケージをダウンロード")
print("\n3. ダウンロードしたファイルを解凍")
print("\n4. MetaTrader5フォルダをPythonのsite-packagesにコピー")

# Pythonのsite-packagesの場所を表示
try:
    import site
    site_packages = site.getsitepackages()
    if site_packages:
        print(f"\n   Pythonのsite-packages: {site_packages[0]}")
        print(f"   コピー先: {os.path.join(site_packages[0], 'MetaTrader5')}")
except:
    pass

print("\n方法2: MT5のインストールディレクトリからコピー")
print("-" * 60)
mt5_path = r"C:\Program Files\MetaTrader 5"
python_api_paths = [
    os.path.join(mt5_path, "MQL5", "Libraries", "Python", "MetaTrader5"),
    os.path.join(mt5_path, "MetaTrader5"),
]

print(f"\nMT5のインストールディレクトリ: {mt5_path}")
print("\n以下のパスを確認してください:")
for path in python_api_paths:
    exists = os.path.exists(path)
    status = "[存在]" if exists else "[不存在]"
    print(f"  {status} {path}")

print("\n方法3: 手動でパッケージをインストール")
print("-" * 60)
print("1. MT5の公式サイトからPython APIパッケージをダウンロード")
print("2. ダウンロードしたファイルを解凍")
print("3. 解凍したMetaTrader5フォルダを、このプロジェクトのディレクトリに配置")
print("4. または、Pythonのsite-packagesにコピー")

print("\n" + "=" * 60)
print("インストール後の確認")
print("=" * 60)
print("\n以下のコマンドで確認できます:")
print("  python test_mt5_connection.py")
print("\nまたは:")
print("  python -c \"import MetaTrader5 as mt5; print('OK')\"")



















