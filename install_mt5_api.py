"""
MetaTrader 5 Python API インストールスクリプト
"""
import subprocess
import sys
import os

def install_mt5_api():
    """MT5のPython APIをインストール"""
    print("=" * 60)
    print("MetaTrader 5 Python API インストール")
    print("=" * 60)
    
    # 方法1: pipでインストールを試す
    print("\n方法1: pipでインストールを試します...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "MetaTrader5"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ MetaTrader5が正常にインストールされました")
            return True
        else:
            print("✗ pipでのインストールに失敗しました")
            print(result.stderr)
    except Exception as e:
        print(f"エラー: {e}")
    
    # 方法2: 別のパッケージ名を試す
    print("\n方法2: 別のパッケージ名を試します...")
    alternative_names = ["meta-trader5", "metatrader5", "mt5"]
    for name in alternative_names:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", name],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✓ {name}が正常にインストールされました")
                return True
        except Exception as e:
            continue
    
    print("\n" + "=" * 60)
    print("インストール方法の案内")
    print("=" * 60)
    print("\nMetaTrader 5のPython APIをインストールするには:")
    print("\n1. MetaTrader 5公式サイトからPython APIをダウンロード")
    print("   https://www.metatrader5.com/ja/download")
    print("\n2. または、以下のコマンドでインストールを試してください:")
    print("   pip install MetaTrader5")
    print("\n3. MT5がインストールされている場合、MT5のインストールディレクトリから")
    print("   Python APIを利用できる場合があります")
    print("\n4. MT5を起動してから、このプログラムを実行してください")
    
    return False

if __name__ == "__main__":
    install_mt5_api()



















