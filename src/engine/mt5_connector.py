"""
MetaTrader 5接続クラス
"""
import os
import sys

# 環境変数を読み込む
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import MetaTrader5 as mt5
except ImportError:
    # MT5のインストールディレクトリをパスに追加して再試行
    possible_paths = [
        r"C:\Program Files\MetaTrader 5",
        r"C:\Program Files (x86)\MetaTrader 5",
        os.path.expanduser(r"~\Desktop\MetaTrader 5"),
    ]
    
    mt5 = None
    for mt5_path in possible_paths:
        if os.path.exists(mt5_path):
            # 複数のパスを試す
            python_api_paths = [
                os.path.join(mt5_path, "MQL5", "Libraries", "Python"),
                os.path.join(mt5_path, "MetaTrader5"),
                mt5_path,  # ルートディレクトリも試す
            ]
            
            for python_api_path in python_api_paths:
                if os.path.exists(python_api_path):
                    if python_api_path not in sys.path:
                        sys.path.insert(0, python_api_path)
                    try:
                        import MetaTrader5 as mt5
                        print(f"[INFO] MT5のPython APIを読み込みました: {python_api_path}")
                        break
                    except ImportError:
                        continue
            
            if mt5 is not None:
                break
    
    if mt5 is None:
        print("=" * 60)
        print("警告: MetaTrader5モジュールが見つかりません")
        print("=" * 60)
        print("\nMT5のPython APIをインストールするには:")
        print("\n方法1: MT5を起動してから実行")
        print("  - MetaTrader 5を起動してください")
        print("  - アカウントにログインしてください")
        print("  - その後、このプログラムを実行してください")
        print("\n方法2: 公式サイトからダウンロード")
        print("  - https://www.mql5.com/ja/docs/integration/python_metatrader5")
        print("  - Python APIパッケージをダウンロードしてインストール")
        print("\n方法3: MT5が起動している状態で、DLLを直接読み込む")
        print("  - MT5を起動している状態で、このプログラムを実行してください")
        print("=" * 60)

import pandas as pd
from datetime import datetime, timedelta
import time


class MT5Connector:
    """MetaTrader 5への接続を管理するクラス"""
    
    def __init__(self, login=None, password=None, server=None, path=None):
        """
        MT5接続を初期化
        
        Args:
            login: MT5アカウント番号（Noneの場合は自動検出）
            password: MT5パスワード（Noneの場合は自動検出）
            server: ブローカーサーバー名（Noneの場合は自動検出）
            path: MT5のインストールパス（Noneの場合は自動検出）
        """
        # 環境変数から取得、なければ引数を使用
        import os
        self.login = login or os.getenv('MT5_LOGIN')
        self.password = password or os.getenv('MT5_PASSWORD')
        self.server = server or os.getenv('MT5_SERVER')
        self.path = path
        self.connected = False
    
    def connect(self):
        """MT5に接続"""
        if mt5 is None:
            print("=" * 60)
            print("エラー: MetaTrader5モジュールが利用できません。")
            print("=" * 60)
            print("\n解決方法:")
            print("1. MetaTrader 5がインストールされているか確認してください")
            print("2. pip install MetaTrader5 を実行してください")
            print("3. または、MT5のインストールディレクトリからPython APIを利用してください")
            return False
        
        # パスの確認
        if self.path:
            print(f"MT5のパスを指定: {self.path}")
            if not os.path.exists(self.path):
                print(f"警告: 指定されたパスが存在しません: {self.path}")
        else:
            print("MT5のパスを自動検出します...")
        
        # MT5を初期化
        print("MT5を初期化しています...")
        # pathがNoneの場合は引数を省略（自動検出）
        if self.path is None:
            init_result = mt5.initialize()
        else:
            init_result = mt5.initialize(path=self.path)
        
        if not init_result:
            error = mt5.last_error()
            error_code = error[0]
            error_description = error[1]
            
            print("=" * 60)
            print("MT5初期化エラー")
            print("=" * 60)
            print(f"エラーコード: {error_code}")
            print(f"エラー説明: {error_description}")
            
            if error_code == -2:  # Invalid "path" argument
                print("\n考えられる原因:")
                print("1. MT5のパスが無効です")
                print(f"   → 現在のパス: {self.path}")
                print("   → MT5のターミナルが既に起動している場合は、パスをNoneに設定してください")
                print("   → または、MT5のインストールディレクトリのパスを正しく指定してください")
            elif error_code == 1:  # RES_S_OK以外
                print("\n考えられる原因:")
                print("1. MetaTrader 5が起動していない")
                print("   → MT5を起動してから再度実行してください")
                print("2. MT5のインストールパスが正しくない")
                print(f"   → 現在のパス: {self.path}")
                print("   → MT5のインストールディレクトリを確認してください")
                print("3. MT5のPython APIが正しくインストールされていない")
                print("   → pip install MetaTrader5 を実行してください")
            elif error_code == 10004:  # TRADE_RETCODE_REQUOTE
                print("\n考えられる原因:")
                print("1. MT5が起動していない")
                print("2. ネットワーク接続の問題")
            else:
                print(f"\n不明なエラーコード: {error_code}")
                print("MT5の公式ドキュメントを確認してください")
            
            return False
        
        print("MT5の初期化に成功しました")
        
        # MT5のプロセスが完全に起動するまで少し待機
        time.sleep(3)  # 待機時間を長くする
        
        # まず、既にログインしているか確認
        account_info = mt5.account_info()
        if account_info is not None:
            print(f"\n既にMT5にログインしています: {account_info.login}")
            print(f"  サーバー: {account_info.server}")
            # 既にログインしている場合、指定されたアカウントと一致するか確認
            if self.login and str(account_info.login) == str(self.login):
                print("指定されたアカウントで既にログイン済みです")
                self.connected = True
                return True
        
        # ログイン情報の確認
        print("\nログイン情報を確認しています...")
        print(f"  アカウント番号: {'設定済み' if self.login else '未設定'}")
        print(f"  パスワード: {'設定済み' if self.password else '未設定'}")
        print(f"  サーバー名: {'設定済み' if self.server else '未設定'}")
        
        # ログイン情報が指定されている場合はログイン
        if self.login and self.password and self.server:
            print(f"\nデモトレード口座にログイン中...")
            print(f"  アカウント: {self.login}")
            print(f"  サーバー: {self.server}")
            
            # アカウント番号を整数に変換（文字列の場合は変換）
            try:
                login_int = int(self.login) if isinstance(self.login, str) else self.login
            except (ValueError, TypeError):
                login_int = self.login
            
            # ログインを複数回試行（リトライロジック）
            max_retries = 3
            retry_delay = 2
            login_success = False
            
            for attempt in range(max_retries):
                if attempt > 0:
                    print(f"\nログイン再試行中... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                
                # MT5のlogin()は位置引数として呼び出す必要がある
                if mt5.login(login_int, self.password, self.server):
                    login_success = True
                    break
                else:
                    error = mt5.last_error()
                    error_code = error[0]
                    error_description = error[1]
                    print(f"  試行 {attempt + 1} 失敗: {error_description}")
            
            if not login_success:
                error = mt5.last_error()
                error_code = error[0]
                error_description = error[1]
                
                print("=" * 60)
                print("MT5ログインエラー")
                print("=" * 60)
                print(f"エラーコード: {error_code}")
                print(f"エラー説明: {error_description}")
                
                if error_code == -10005:  # IPC timeout
                    print("\n【重要】IPC timeoutエラー")
                    print("MT5のターミナルとの通信が確立されていません。")
                    print("\n対処法:")
                    print("1. MetaTrader 5のターミナルを手動で起動してください")
                    print("2. MT5のターミナルで手動ログインしてください:")
                    print(f"   - アカウント: {self.login}")
                    print(f"   - パスワード: {'*' * len(self.password)}")
                    print(f"   - サーバー: {self.server}")
                    print("3. MT5のターミナルでログインが成功したことを確認してください")
                    print("4. MT5のターミナルが起動した状態で、このプログラムを再度実行してください")
                    print("\n注意:")
                    print("- MT5のターミナルを起動してから、このプログラムを実行してください")
                    print("- MT5のターミナルで手動ログインが成功する必要があります")
                    print("- ターミナルを起動した後、数秒待ってからプログラムを実行してください")
                else:
                    print("\n考えられる原因:")
                    print("1. アカウント番号が間違っている")
                    print("2. パスワードが間違っている")
                    print("3. サーバー名が間違っている（デモサーバー名を確認してください）")
                    print("4. アカウントが無効化されている")
                    print("5. ネットワーク接続の問題")
                    print("\n確認事項:")
                    print("- MT5のターミナルで手動ログインできるか確認してください")
                    print("- デモサーバー名は通常、ブローカー名の後に「- Demo」が付きます")
                    print("- 例: 「YourBroker-Demo」または「YourBroker Demo」")
                
                mt5.shutdown()
                return False
            
            print(f"✓ MT5にログインしました: {self.login}")
        else:
            # 自動ログイン（既にMT5が起動している場合）
            print("\n自動ログインを試みます（MT5が既に起動している場合）...")
            account_info = mt5.account_info()
            if account_info is None:
                print("=" * 60)
                print("MT5アカウント情報を取得できませんでした")
                print("=" * 60)
                print("\n考えられる原因:")
                print("1. MT5が起動していない")
                print("   → MT5を起動してアカウントにログインしてください")
                print("2. ログイン情報が設定されていない")
                print("   → .envファイルに以下を設定してください:")
                print("     MT5_LOGIN=あなたのアカウント番号")
                print("     MT5_PASSWORD=あなたのパスワード")
                print("     MT5_SERVER=あなたのブローカーのデモサーバー名")
                print("\nまたは、main.pyでMT5Connectorに直接ログイン情報を渡してください")
                
                mt5.shutdown()
                return False
            
            print(f"✓ MT5に接続しました: {account_info.login}")
            print(f"  サーバー: {account_info.server}")
            print(f"  残高: {account_info.balance:.2f} {account_info.currency}")
        
        self.connected = True
        return True
    
    def disconnect(self):
        """MT5から切断"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("MT5から切断しました")
    
    def get_account_info(self):
        """アカウント情報を取得"""
        if not self.connected:
            return None
        return mt5.account_info()
    
    def get_rates(self, symbol, timeframe=None, count=100):
        """
        レートデータを取得
        
        Args:
            symbol: 通貨ペア（例: "EURUSD"）
            timeframe: 時間足（デフォルト: H1）
            count: 取得するローソク足の数
        
        Returns:
            pandas.DataFrame: OHLCデータ
        """
        if mt5 is None:
            print("MetaTrader5モジュールが利用できません")
            return None
        
        if timeframe is None:
            timeframe = mt5.TIMEFRAME_H1
        
        if not self.connected:
            print("MT5に接続されていません")
            return None
        
        # MT5の接続状態を再確認
        account_info = mt5.account_info()
        if account_info is None:
            print(f"[警告] MT5の接続が切れている可能性があります。シンボル {symbol} の取得をスキップします")
            self.connected = False
            return None
        
        # シンボル情報を取得
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"シンボル {symbol} が見つかりません")
            print(f"[デバッグ] MT5接続状態: {'接続中' if self.connected else '未接続'}")
            print(f"[デバッグ] アカウント情報: {'取得可能' if account_info else '取得不可'}")
            # 利用可能なシンボルを確認（デバッグ用）
            try:
                symbols_total = mt5.symbols_total()
                print(f"[デバッグ] MT5で利用可能なシンボル数: {symbols_total}")
            except:
                pass
            return None
        
        # シンボルが有効でない場合は有効化
        if not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                print(f"シンボル {symbol} を有効化できませんでした")
                return None
        
        # レートデータを取得
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        
        if rates is None or len(rates) == 0:
            print(f"レートデータを取得できませんでした: {mt5.last_error()}")
            return None
        
        # DataFrameに変換
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # カラム名を小文字に統一
        df.columns = df.columns.str.lower()
        
        return df
    
    def get_current_price(self, symbol):
        """現在の価格を取得"""
        if not self.connected:
            return None
        
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
        
        return {
            'bid': tick.bid,
            'ask': tick.ask,
            'last': tick.last,
            'time': datetime.fromtimestamp(tick.time)
        }
    
    def place_order(self, symbol, order_type, volume, price=None, sl=None, tp=None, comment="", magic=None):
        """
        注文を送信
        
        Args:
            symbol: 通貨ペア
            order_type: 注文タイプ（mt5.ORDER_TYPE_BUY または mt5.ORDER_TYPE_SELL）
            volume: ロット数
            price: 価格（Noneの場合は成行）
            sl: 損切り価格
            tp: 利確価格
            comment: コメント
            magic: Magic number（戦略識別用、Noneの場合はデフォルト値234000を使用）
        
        Returns:
            tuple: (success, ticket, result) または (False, None, None)
                   success=Trueの場合、resultはMT5のorder_sendの戻り値
        """
        if not self.connected:
            print("MT5に接続されていません")
            return False, None, None
        
        # MT5の接続状態を再確認
        account_info = mt5.account_info()
        if account_info is None:
            print(f"[警告] MT5の接続が切れている可能性があります。注文を送信できません")
            self.connected = False
            return False, None, None
        
        # シンボル情報を取得
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"シンボル {symbol} が見つかりません")
            print(f"[デバッグ] MT5接続状態: {'接続中' if self.connected else '未接続'}")
            print(f"[デバッグ] アカウント情報: {'取得可能' if account_info else '取得不可'}")
            return False, None, None
        
        # 価格が指定されていない場合は成行注文
        if price is None:
            if order_type == mt5.ORDER_TYPE_BUY:
                price = mt5.symbol_info_tick(symbol).ask
            else:
                price = mt5.symbol_info_tick(symbol).bid
        
        # リクエストを作成
        # magic numberが指定されていない場合はデフォルト値を使用
        magic_number = magic if magic is not None else 234000
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": magic_number,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # SLとTPは値がある場合のみ追加（MT5では0を設定するとエラーになる場合がある）
        if sl and sl > 0:
            request["sl"] = sl
        if tp and tp > 0:
            request["tp"] = tp
        
        # 注文を送信
        result = mt5.order_send(request)
        
        # resultがNoneの場合のエラーハンドリング
        if result is None:
            error_code = mt5.last_error()
            print(f"注文送信エラー: result is None (エラーコード: {error_code})")
            print(f"リクエスト内容: {request}")
            return False, None, None
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            error_code = result.retcode
            error_comment = result.comment
            print(f"注文エラー: {error_code} - {error_comment}")
            
            # エラー10026: AutoTrading disabled by server
            if error_code == 10026:
                print("\n" + "=" * 60)
                print("【重要】サーバー側で自動取引が無効になっています")
                print("=" * 60)
                print("\nこのエラーは、ブローカーのサーバー側で自動取引が制限されている場合に発生します。")
                print("\n考えられる原因:")
                print("1. デモ口座で自動取引が制限されている")
                print("2. ブローカーの設定で自動取引が無効になっている")
                print("3. アカウントタイプによって自動取引が許可されていない")
                print("\n対処法:")
                print("1. ブローカーのサポートに連絡して、自動取引が有効か確認してください")
                print("2. アカウント設定で自動取引が有効になっているか確認してください")
                print("3. 別のアカウントタイプ（例：リアル口座）で試してください")
                print("4. ブローカーのウェブサイトで自動取引の設定を確認してください")
                print("\n注意: 一部のブローカーでは、デモ口座で自動取引が制限されている場合があります。")
                print("=" * 60)
            # エラー10027: AutoTrading disabled by client
            elif error_code == 10027:
                print("\n" + "=" * 60)
                print("【重要】自動取引が無効になっています")
                print("=" * 60)
                print("\nMT5のターミナルで自動取引を有効にする必要があります。")
                print("\n手順:")
                print("1. MT5のターミナルを開く")
                print("2. ツール → オプション → エキスパートアドバイザー")
                print("3. 「自動取引を許可する」にチェックを入れる")
                print("4. または、MT5のターミナルのツールバーで「自動取引」ボタンをクリック")
                print("   （通常、ツールバーの上部に「AutoTrading」ボタンがあります）")
                print("5. ボタンが緑色になったことを確認してください")
                print("6. その後、このプログラムを再度実行してください")
                print("=" * 60)
            
            return False, None, None
        
        print(f"注文が成功しました: チケット={result.order}, シンボル={symbol}, タイプ={order_type}, ロット={volume}")
        return True, result.order, result
    
    def close_position(self, ticket):
        """
        ポジションを決済
        
        Args:
            ticket: ポジションのチケット番号
        
        Returns:
            tuple: (success, profit, balance_after) または (False, None, None)
                   success=Trueの場合、profitは利益、balance_afterは決済後の残高
        """
        if not self.connected:
            return False, None, None
        
        # ポジション情報を取得
        position = mt5.positions_get(ticket=ticket)
        if position is None or len(position) == 0:
            print(f"ポジション {ticket} が見つかりません")
            return False, None, None
        
        position = position[0]
        
        # 決済前の利益を取得
        profit_before = position.profit
        
        # 決済注文を作成
        order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": order_type,
            "position": ticket,
            "deviation": 20,
            "magic": 234000,
            "comment": "Close position",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"決済エラー: {result.retcode} - {result.comment}")
            return False, None, None
        
        # 決済後の残高を取得
        account_info = mt5.account_info()
        balance_after = account_info.balance if account_info else None
        
        print(f"ポジション {ticket} を決済しました（利益: {profit_before:.2f}）")
        return True, profit_before, balance_after
    
    def get_positions(self, symbol=None, magic=None):
        """
        開いているポジションを取得
        
        Args:
            symbol: シンボル名（Noneの場合はすべてのシンボル）
            magic: Magic number（Noneの場合はすべてのmagic number）
        
        Returns:
            list: ポジションのリスト
        """
        if not self.connected:
            return []
        
        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()
        
        if positions is None:
            return []
        
        # magic numberでフィルタリング
        if magic is not None:
            positions = [pos for pos in positions if pos.magic == magic]
        
        return positions

