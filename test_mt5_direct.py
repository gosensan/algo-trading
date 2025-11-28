"""
MT5直接接続テスト（DLLを直接読み込む）
"""
import os
import sys
import ctypes

print("=" * 60)
print("MT5直接接続テスト（DLL読み込み）")
print("=" * 60)

# MT5のインストールディレクトリ
mt5_path = r"C:\Program Files\MetaTrader 5"

# MT5のDLLファイルを検索
dll_files = [
    "terminal64.dll",
    "MT5Terminal64.dll",
    "MetaTrader5.dll",
]

print(f"\nMT5のインストールディレクトリ: {mt5_path}")

found_dll = None
for dll_name in dll_files:
    dll_path = os.path.join(mt5_path, dll_name)
    if os.path.exists(dll_path):
        print(f"[OK] DLLが見つかりました: {dll_name}")
        found_dll = dll_path
        break

if not found_dll:
    print("[NG] MT5のDLLファイルが見つかりませんでした")
    sys.exit(1)

# DLLを読み込んでみる
try:
    print(f"\nDLLを読み込み中: {found_dll}")
    dll = ctypes.CDLL(found_dll)
    print("[OK] DLLの読み込みに成功しました")
    
    # MT5の初期化関数を探す
    # 実際の関数名はMT5のバージョンによって異なる可能性があります
    print("\n注意: DLLを直接読み込む方法は、MT5のPython APIとは異なります")
    print("MT5のPython APIを使用するには、公式サイトからダウンロードする必要があります")
    
except Exception as e:
    print(f"[NG] DLLの読み込みに失敗: {e}")

print("\n" + "=" * 60)
print("推奨される解決方法")
print("=" * 60)
print("\nMT5のPython APIを使用するには:")
print("1. MT5の公式サイトからPython APIをダウンロード")
print("   https://www.mql5.com/ja/docs/integration/python_metatrader5")
print("\n2. または、MT5のインストールディレクトリにPython APIが含まれているか確認")
print("   通常は: C:\\Program Files\\MetaTrader 5\\MQL5\\Libraries\\Python")
print("\n3. MT5が起動している状態で、Python APIパッケージをインストール")



















