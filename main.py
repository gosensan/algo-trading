"""
メインエントリーポイント
"""
import sys
import os
from src.engine.mt5_connector import MT5Connector
from src.engine.executor import TradeExecutor
from src.strategies.bollinger import BollingerStrategy
from src.strategies.donchian import DonchianStrategy

try:
    import MetaTrader5 as mt5
except ImportError:
    print("エラー: MetaTrader5モジュールが見つかりません。")
    print("\nMetaTrader 5のPython APIをインストールするには:")
    print("1. MetaTrader 5をインストールしてください")
    print("2. MT5のインストールディレクトリからPython APIを利用できます")
    print("3. または、MT5のPython APIパッケージをインストールしてください")
    sys.exit(1)


def main():
    """メイン関数"""
    print("=" * 60)
    print("アルゴリズムトレーディングシステム")
    print("=" * 60)
    print("\n【重要】MT5のターミナルを起動してください")
    print("1. MetaTrader 5のターミナルを手動で起動してください")
    print("2. MT5のターミナルでログインしてください（.envファイルに設定した情報を使用）")
    print("3. MT5のターミナルでログインが成功したことを確認してください")
    print("4. その後、このプログラムが続行します...")
    print("=" * 60 + "\n")
    
    # ============================================================
    # デモトレード口座への接続設定
    # ============================================================
    # 方法1: .envファイルを使用（推奨）
    # プロジェクトルートに .env ファイルを作成し、以下を設定:
    #   MT5_LOGIN=あなたのアカウント番号
    #   MT5_PASSWORD=あなたのパスワード
    #   MT5_SERVER=あなたのブローカーのデモサーバー名
    #
    # 方法2: 直接ここに設定（.envファイルがない場合）
    # 以下の3行のコメントを外して、実際の値を設定してください:
    # MT5_LOGIN = "12345678"  # デモトレード口座のアカウント番号
    # MT5_PASSWORD = "your_password"  # デモトレード口座のパスワード
    # MT5_SERVER = "YourBroker-Demo"  # デモサーバー名（MT5のターミナルで確認）
    
    # デモトレード口座への接続情報を設定
    # セキュリティのため、.envファイルを使用してください（推奨）
    # プロジェクトルートに .env ファイルを作成し、以下を設定:
    #   MT5_LOGIN=あなたのアカウント番号
    #   MT5_PASSWORD=あなたのパスワード
    #   MT5_SERVER=あなたのブローカーのサーバー名
    
    # 環境変数から取得
    try:
        from dotenv import load_dotenv
        # プロジェクトルートの.envファイルを明示的に読み込む
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        load_dotenv(dotenv_path=env_path)
    except ImportError:
        print("警告: python-dotenvがインストールされていません。")
        print("pip install python-dotenv でインストールしてください。")
        # python-dotenvがない場合、.envファイルを直接読み込む
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
    
    MT5_LOGIN = os.getenv('MT5_LOGIN')
    MT5_PASSWORD = os.getenv('MT5_PASSWORD')
    MT5_SERVER = os.getenv('MT5_SERVER')
    
    # デバッグ用: 環境変数が読み込まれたか確認
    print(f"\n[デバッグ] 環境変数の読み込み状況:")
    print(f"  MT5_LOGIN: {'設定済み' if MT5_LOGIN else '未設定'}")
    print(f"  MT5_PASSWORD: {'設定済み' if MT5_PASSWORD else '未設定'}")
    print(f"  MT5_SERVER: {'設定済み' if MT5_SERVER else '未設定'}")
    
    # .envファイルが設定されていない場合の警告
    if not MT5_LOGIN or not MT5_PASSWORD or not MT5_SERVER:
        print("\n" + "=" * 60)
        print("【重要】ログイン情報が設定されていません")
        print("=" * 60)
        print("\nプロジェクトルートに .env ファイルを作成し、以下を設定してください:")
        print("  MT5_LOGIN=あなたのアカウント番号")
        print("  MT5_PASSWORD=あなたのパスワード")
        print("  MT5_SERVER=あなたのブローカーのサーバー名")
        print("\n例:")
        print("  MT5_LOGIN=12345678")
        print("  MT5_PASSWORD=your_password")
        print("  MT5_SERVER=YourBroker-Demo")
        print("\n注意: .envファイルは.gitignoreに含まれているため、GitHubにアップロードされません。")
        print("=" * 60 + "\n")
        return
    
    # MT5接続を初期化
    # MT5のターミナルが既に起動している場合は、Noneを渡して自動検出させる（推奨）
    # MT5のターミナルを手動で起動してログインした後、このプログラムを実行してください
    mt5_path = None  # Noneを指定すると、MT5が自動的に検出されます
    
    # もしMT5のターミナルが起動していない場合は、以下のコメントを外してパスを指定できます
    # possible_paths = [
    #     r"C:\Program Files\MetaTrader 5\terminal64.exe",
    #     r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
    #     os.path.expanduser(r"~\Desktop\MetaTrader 5\terminal64.exe"),
    # ]
    # for path in possible_paths:
    #     if os.path.exists(path):
    #         mt5_path = path
    #         print(f"MT5のパスを検出: {mt5_path}")
    #         break
    
    # MT5接続を作成（ログイン情報を渡す）
    mt5_connector = MT5Connector(
        login=MT5_LOGIN,
        password=MT5_PASSWORD,
        server=MT5_SERVER,
        path=mt5_path
    )
    
    # MT5に接続
    print("\nMT5に接続中...")
    if not mt5_connector.connect():
        print("\n" + "=" * 60)
        print("接続に失敗しました")
        print("=" * 60)
        print("\n上記のエラーメッセージを確認してください。")
        print("\nデモトレード口座への接続には以下が必要です:")
        print("1. アカウント番号（MT5_LOGIN）")
        print("2. パスワード（MT5_PASSWORD）")
        print("3. デモサーバー名（MT5_SERVER）")
        print("\n設定方法:")
        print("- .envファイルを作成して設定する（推奨）")
        print("- または、main.pyのMT5_LOGIN, MT5_PASSWORD, MT5_SERVERを直接設定する")
        return
    
    # アカウント情報を表示
    account_info = mt5_connector.get_account_info()
    if account_info:
        print(f"\nアカウント情報:")
        print(f"  アカウント番号: {account_info.login}")
        print(f"  残高: {account_info.balance:.2f} {account_info.currency}")
        print(f"  証拠金: {account_info.margin:.2f}")
        print(f"  有効証拠金: {account_info.margin_free:.2f}")
    
    # 戦略を初期化（複数戦略を並列実行）
    # 本番仕様: ドンチャンはXAUUSD（4時間足）、ボリンジャーはEURUSD（4時間足）
    donchian_symbol = "XAUUSD"
    bollinger_symbol = "EURUSD"
    
    # ドンチャンブレイクアウト戦略（4時間足10期間）- XAUUSD
    donchian_strategy = DonchianStrategy(symbol=donchian_symbol, period=10)
    
    # ボリンジャーバンド戦略（4時間足）- EURUSD
    bollinger_strategy = BollingerStrategy(symbol=bollinger_symbol)
    
    # 複数戦略をリストに追加
    strategies = [donchian_strategy, bollinger_strategy]
    
    # 戦略ごとのロットサイズを設定
    # シンボル名または戦略名で指定可能
    strategy_lot_sizes = {
        donchian_symbol: 0.01,  # XAUUSD用のロットサイズ
        bollinger_symbol: 0.1,  # EURUSD用のロットサイズ
        # または戦略名で指定することも可能:
        # donchian_strategy.name: 0.01,
        # bollinger_strategy.name: 0.01,
    }
    
    # トレード実行エンジンを初期化（複数戦略対応）
    # 注意: 各戦略が異なるシンボルを使用する場合、symbolパラメータは最初の戦略のシンボルを使用（後方互換性のため）
    default_lot_size = 0.01  # デフォルトロットサイズ（strategy_lot_sizesで指定されていない場合に使用）
    executor = TradeExecutor(
        mt5_connector=mt5_connector,
        symbol=donchian_symbol,  # 後方互換性のため（実際には各戦略のシンボルが使用される）
        lot_size=default_lot_size,
        strategies=strategies,
        strategy_lot_sizes=strategy_lot_sizes
    )
    
    # 各戦略の時間足を設定（両方とも4時間足）
    strategy_timeframes = {
        donchian_strategy.name: mt5.TIMEFRAME_H4,  # ドンチャン: 4時間足
        bollinger_strategy.name: mt5.TIMEFRAME_H4  # ボリンジャー: 4時間足
    }
    
    # 戦略を実行
    print("\n" + "=" * 60)
    print("戦略を開始します...")
    print(f"実行戦略数: {len(strategies)}")
    print(f"  1. ドンチャンブレイクアウト ({donchian_strategy.name})")
    print(f"     - シンボル: {donchian_symbol}")
    print(f"     - Magic Number: {donchian_strategy.magic}")
    print(f"     - 時間足: H4 (4時間足)")
    print(f"     - ドンチャン期間: 10期間")
    print(f"     - 決済条件: 4時間足12本クローズ")
    print(f"  2. ボリンジャーバンド ({bollinger_strategy.name})")
    print(f"     - シンボル: {bollinger_symbol}")
    print(f"     - Magic Number: {bollinger_strategy.magic}")
    print(f"     - 時間足: H4 (4時間足)")
    print(f"     - 決済条件: 中央線到達、または4時間足18本クローズ")
    print(f"\nロットサイズ設定:")
    for strategy in strategies:
        strategy_lot = strategy_lot_sizes.get(strategy.symbol, strategy_lot_sizes.get(strategy.name, default_lot_size))
        print(f"  - {strategy.name} ({strategy.symbol}): {strategy_lot}")
    print("\nポジション管理:")
    print("  - 各戦略は最大1ポジションのみ保有（magic number + symbolで管理）")
    print("  - 合計最大2ポジション（両戦略同時稼働可能）")
    print("エントリー制限: 各戦略1日1回（最大1日2回）")
    print("チェック間隔: 300秒（5分）")
    print("停止するには Ctrl+C を押してください")
    print("=" * 60 + "\n")
    
    try:
        executor.run(strategy_timeframes=strategy_timeframes, check_interval=300)  # 本番用: 5分ごとにチェック
    except KeyboardInterrupt:
        print("\n\n戦略を停止しました")
    finally:
        # MT5から切断
        mt5_connector.disconnect()
        print("プログラムを終了します")


if __name__ == "__main__":
    main()



