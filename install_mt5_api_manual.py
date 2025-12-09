"""
MT5 Python API 手動インストールスクリプト
MT5のDLLを直接読み込む方法を試します
"""
import os
import sys
import ctypes

def find_mt5_dll():
    """MT5のDLLファイルを検索"""
    possible_paths = [
        r"C:\Program Files\MetaTrader 5",
        r"C:\Program Files (x86)\MetaTrader 5",
        os.path.expanduser(r"~\Desktop\MetaTrader 5"),
    ]
    
    dll_names = [
        "terminal64.dll",
        "MT5Terminal64.dll",
        "MetaTrader5.dll",
        "mt5.dll",
    ]
    
    for mt5_path in possible_paths:
        if os.path.exists(mt5_path):
            for dll_name in dll_names:
                dll_path = os.path.join(mt5_path, dll_name)
                if os.path.exists(dll_path):
                    return dll_path
    
    return None

def install_mt5_api_from_source():
    """MT5のPython APIをソースからインストール"""
    print("=" * 60)
    print("MT5 Python API 手動インストール")
    print("=" * 60)
    
    # 方法1: MT5のDLLを直接読み込む
    print("\n方法1: MT5のDLLを検索中...")
    dll_path = find_mt5_dll()
    if dll_path:
        print(f"  DLLが見つかりました: {dll_path}")
        try:
            # DLLを読み込んでみる
            dll = ctypes.CDLL(dll_path)
            print("  DLLの読み込みに成功しました")
        except Exception as e:
            print(f"  DLLの読み込みに失敗: {e}")
    else:
        print("  DLLが見つかりませんでした")
    
    # 方法2: MT5のPython APIパッケージをダウンロード
    print("\n方法2: MT5公式サイトからPython APIをダウンロード")
    print("  以下のURLからPython APIをダウンロードしてください:")
    print("  https://www.metatrader5.com/ja/download")
    print("  または")
    print("  https://www.mql5.com/ja/docs/integration/python_metatrader5")
    
    # 方法3: GitHubからインストール
    print("\n方法3: GitHubからインストールを試す")
    print("  以下のコマンドを試してください:")
    print("  pip install git+https://github.com/MetaQuotes/MetaTrader5.git")
    
    return False

if __name__ == "__main__":
    install_mt5_api_from_source()



















