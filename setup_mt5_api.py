"""
MT5 Python API セットアップスクリプト
MT5のインストールディレクトリからPython APIをセットアップします
"""
import os
import sys
import shutil

def setup_mt5_api():
    """MT5のPython APIをセットアップ"""
    print("=" * 60)
    print("MT5 Python API セットアップ")
    print("=" * 60)
    
    # MT5のインストールディレクトリを検索
    possible_paths = [
        r"C:\Program Files\MetaTrader 5",
        r"C:\Program Files (x86)\MetaTrader 5",
        os.path.expanduser(r"~\Desktop\MetaTrader 5"),
    ]
    
    mt5_path = None
    for path in possible_paths:
        if os.path.exists(path):
            mt5_path = path
            print(f"\nMT5が見つかりました: {mt5_path}")
            break
    
    if not mt5_path:
        print("\n[NG] MT5のインストールディレクトリが見つかりませんでした")
        return False
    
    # Python APIのパスを確認
    python_api_paths = [
        os.path.join(mt5_path, "MQL5", "Libraries", "Python", "MetaTrader5"),
        os.path.join(mt5_path, "MQL5", "Libraries", "Python"),
        os.path.join(mt5_path, "MetaTrader5"),
    ]
    
    print("\nPython APIのパスを確認中...")
    for api_path in python_api_paths:
        if os.path.exists(api_path):
            print(f"  [OK] Python APIが見つかりました: {api_path}")
            
            # Pythonのsite-packagesにコピーを試す
            try:
                import site
                site_packages = site.getsitepackages()[0] if site.getsitepackages() else None
                if site_packages:
                    target_path = os.path.join(site_packages, "MetaTrader5")
                    print(f"\n  site-packagesにコピーを試します: {target_path}")
                    
                    if os.path.exists(target_path):
                        print(f"  [INFO] 既に存在します: {target_path}")
                    else:
                        # シンボリックリンクまたはコピーを作成
                        if hasattr(os, 'symlink'):
                            try:
                                os.symlink(api_path, target_path)
                                print(f"  [OK] シンボリックリンクを作成しました")
                            except:
                                shutil.copytree(api_path, target_path)
                                print(f"  [OK] コピーを作成しました")
                        else:
                            shutil.copytree(api_path, target_path)
                            print(f"  [OK] コピーを作成しました")
                    
                    # パスに追加
                    if api_path not in sys.path:
                        sys.path.insert(0, api_path)
                        print(f"  [OK] Pythonパスに追加しました")
                    
                    return True
            except Exception as e:
                print(f"  [NG] エラー: {e}")
                # パスに追加するだけでも試す
                if api_path not in sys.path:
                    sys.path.insert(0, api_path)
                    print(f"  [INFO] Pythonパスに追加しました（コピーはスキップ）")
                    return True
    
    print("\n[NG] Python APIが見つかりませんでした")
    print("\n解決方法:")
    print("1. MT5を起動してください")
    print("2. MT5の公式サイトからPython APIをダウンロードしてください")
    print("3. または、MT5が起動している状態で、このプログラムを実行してください")
    
    return False

if __name__ == "__main__":
    success = setup_mt5_api()
    if success:
        print("\n" + "=" * 60)
        print("セットアップが完了しました！")
        print("=" * 60)
        print("\n以下のコマンドでテストできます:")
        print("python test_mt5_connection.py")
    else:
        print("\n" + "=" * 60)
        print("セットアップに失敗しました")
        print("=" * 60)
        print("\n別の方法を試してください:")
        print("1. MT5を起動してから、python test_mt5_connection.py を実行")
        print("2. MT5の公式サイトからPython APIをダウンロード")



















