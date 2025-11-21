"""
MT5接続テストスクリプト
"""
import sys
import os

# 環境変数を読み込む
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

print("=" * 60)
print("MT5接続テスト")
print("=" * 60)

# MetaTrader5モジュールのインポートを試す
print("\n1. MetaTrader5モジュールのインポートを試します...")
try:
    import MetaTrader5 as mt5
    print("[OK] MetaTrader5モジュールが見つかりました")
except ImportError:
    print("[NG] MetaTrader5モジュールが見つかりません")
    print("\nMT5のインストールディレクトリを検索中...")
    
    # MT5のインストールディレクトリを検索
    possible_paths = [
        r"C:\Program Files\MetaTrader 5",
        r"C:\Program Files (x86)\MetaTrader 5",
        os.path.expanduser(r"~\Desktop\MetaTrader 5"),
    ]
    
    for mt5_path in possible_paths:
        if os.path.exists(mt5_path):
            print(f"  MT5が見つかりました: {mt5_path}")
            python_api_path = os.path.join(mt5_path, "MQL5", "Libraries", "Python")
            if os.path.exists(python_api_path):
                print(f"  Python APIパス: {python_api_path}")
                sys.path.insert(0, python_api_path)
                try:
                    import MetaTrader5 as mt5
                    print("[OK] MT5のインストールディレクトリからPython APIを読み込みました")
                    break
                except ImportError:
                    continue
    
    if 'mt5' not in globals():
        print("\n[NG] MT5のPython APIが見つかりませんでした")
        print("\n解決方法:")
        print("1. MetaTrader 5が起動しているか確認してください")
        print("2. MT5にアカウントでログインしているか確認してください")
        print("3. MT5を再起動してから再度試してください")
        sys.exit(1)

# MT5の初期化を試す
print("\n2. MT5の初期化を試します...")
if mt5.initialize():
    print("[OK] MT5の初期化に成功しました")
    
    # アカウント情報を取得
    account_info = mt5.account_info()
    if account_info:
        print(f"\nアカウント情報:")
        print(f"  アカウント番号: {account_info.login}")
        print(f"  残高: {account_info.balance:.2f} {account_info.currency}")
        print(f"  サーバー: {account_info.server}")
    
    mt5.shutdown()
    print("\n[OK] MT5接続テストが成功しました！")
else:
    error = mt5.last_error()
    print(f"[NG] MT5の初期化に失敗しました: {error}")
    print("\n確認事項:")
    print("1. MetaTrader 5が起動しているか")
    print("2. MT5にアカウントでログインしているか")
    print("3. MT5のインストールパスが正しいか")
    sys.exit(1)

