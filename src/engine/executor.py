"""
トレード実行エンジン
"""
import time
from datetime import datetime
import pandas as pd
from .mt5_connector import MT5Connector
from .trade_logger import TradeLogger
from .risk_manager import RiskManager

try:
    import MetaTrader5 as mt5
except ImportError:
    print("エラー: MetaTrader5モジュールが見つかりません。")
    mt5 = None


class TradeExecutor:
    """トレードの実行を管理するクラス"""
    
    def __init__(self, mt5_connector, symbol="EURUSD", lot_size=0.01, strategy=None, strategies=None, strategy_lot_sizes=None):
        """
        トレード実行エンジンを初期化
        
        Args:
            mt5_connector: MT5Connectorインスタンス
            symbol: 取引する通貨ペア
            lot_size: ロットサイズ（デフォルト値、strategy_lot_sizesが指定されていない場合に使用）
            strategy: 使用する戦略（BollingerStrategyなど）- 後方互換性のため残す（オプショナル）
            strategies: 複数戦略のリスト（指定された場合はこちらを使用）
            strategy_lot_sizes: 戦略ごとのロットサイズの辞書 {strategy_name: lot_size} または {symbol: lot_size}
        """
        # 複数戦略対応
        if strategies is not None:
            self.strategies = strategies if isinstance(strategies, list) else [strategies]
        elif strategy is not None:
            self.strategies = [strategy]
        else:
            self.strategies = []
        
        # 後方互換性のため、最初の戦略をself.strategyに設定
        self.strategy = self.strategies[0] if len(self.strategies) > 0 else None
        
        self.mt5 = mt5_connector
        self.symbol = symbol
        self.lot_size = lot_size  # デフォルトロットサイズ（後方互換性のため）
        self.strategy_lot_sizes = strategy_lot_sizes if strategy_lot_sizes is not None else {}  # 戦略ごとのロットサイズ
        self.positions = {}  # ポジション管理: {ticket: position_info}
        self.strategy_timeframes = {}  # 各戦略の時間足を管理: {strategy_name: timeframe}
        
        # トレードロガーを初期化
        self.trade_logger = TradeLogger()
        
        # リスクマネージャーを初期化
        self.risk_manager = RiskManager()
        
        # 日初の残高を記録（日次損失計算用）
        account_info = self.mt5.get_account_info()
        self.initial_balance = account_info.balance if account_info else 0.0
    
    def _get_lot_size(self, strategy):
        """
        戦略に応じたロットサイズを取得
        
        Args:
            strategy: 戦略インスタンス
            
        Returns:
            float: ロットサイズ
        """
        # 戦略名で検索
        if strategy.name in self.strategy_lot_sizes:
            return self.strategy_lot_sizes[strategy.name]
        
        # シンボルで検索
        if hasattr(strategy, 'symbol') and strategy.symbol in self.strategy_lot_sizes:
            return self.strategy_lot_sizes[strategy.symbol]
        
        # デフォルトロットサイズを返す
        return self.lot_size
    
    def _has_open_position(self, symbol, magic_number):
        """
        同じmagic numberのポジションが開いているか確認
        
        Args:
            symbol: シンボル名
            magic_number: Magic number
            
        Returns:
            bool: ポジションが存在する場合True
        """
        if mt5 is None:
            return False
        
        positions = self.mt5.get_positions(symbol=symbol, magic=magic_number)
        return len(positions) > 0
    
    def run(self, timeframe=None, check_interval=60, strategy_timeframes=None):
        """
        戦略を実行（継続的に監視）
        
        Args:
            timeframe: 時間足（Noneの場合はH1）- 単一戦略の場合のデフォルト
            check_interval: チェック間隔（秒）
            strategy_timeframes: 各戦略の時間足の辞書 {strategy_name: timeframe}
        """
        if mt5 is None:
            print("エラー: MetaTrader5モジュールが利用できません。")
            return
        
        if timeframe is None:
            timeframe = mt5.TIMEFRAME_H1
        
        # 各戦略の時間足を設定
        if strategy_timeframes:
            self.strategy_timeframes = strategy_timeframes
        else:
            # デフォルト: すべての戦略に同じ時間足を使用
            for strategy in self.strategies:
                self.strategy_timeframes[strategy.name] = timeframe
        
        # メッセージはmain.pyで表示されるため、ここでは表示しない
        # print(f"戦略を開始します: {self.strategy.name}")
        # print(f"シンボル: {self.symbol}, ロットサイズ: {self.lot_size}")
        # print(f"チェック間隔: {check_interval}秒")
        # print("-" * 60)
        
        try:
            while True:
                # 現在のポジションを更新
                self._update_positions()
                
                # 各戦略に対してエントリー判定
                for strategy in self.strategies:
                    strategy_timeframe = self.strategy_timeframes.get(strategy.name, timeframe)
                    self._check_entry(strategy, strategy_timeframe)
                
                # 各戦略に対してエグジット判定
                for strategy in self.strategies:
                    strategy_timeframe = self.strategy_timeframes.get(strategy.name, timeframe)
                    self._check_exit(strategy, strategy_timeframe)
                
                # 待機
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n戦略を停止します...")
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_positions(self):
        """開いているポジションを更新"""
        # 日次統計のリセットチェック
        current_date = datetime.now().date()
        if hasattr(self, 'last_date_check'):
            if self.last_date_check != current_date:
                # 日付が変わった場合、日初の残高を更新
                account_info = self.mt5.get_account_info()
                if account_info:
                    self.initial_balance = account_info.balance
                    # リスクマネージャーの日次統計をリセット
                    self.risk_manager.daily_stats = {
                        "daily_pnl": 0.0,
                        "consecutive_losses": 0,
                        "last_reset_date": current_date,
                        "daily_trades": []
                    }
        else:
            self.last_date_check = current_date
        
        # すべての戦略で使用されるシンボルのポジションを取得
        symbols = set()
        for strategy in self.strategies:
            if hasattr(strategy, 'symbol'):
                symbols.add(strategy.symbol)
        if not symbols:
            symbols.add(self.symbol)  # フォールバック
        
        # すべてのシンボルのポジションを取得
        current_positions = []
        for symbol in symbols:
            positions = self.mt5.get_positions(symbol)
            if positions:
                current_positions.extend(positions)
        
        # 既存のポジションを更新
        for pos in current_positions:
            ticket = pos.ticket
            
            # エントリー時刻を取得（MT5のポジション時刻を使用）
            entry_time = datetime.fromtimestamp(pos.time)
            
            if ticket not in self.positions:
                # 新しいポジション
                self.positions[ticket] = {
                    'ticket': ticket,
                    'side': 'buy' if pos.type == mt5.ORDER_TYPE_BUY else 'sell',
                    'entry_price': pos.price_open,
                    'entry_time': entry_time,  # エントリー時刻を確実に保存
                    'volume': pos.volume,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'comment': pos.comment,  # コメントを保存（戦略名を含む）
                    'symbol': pos.symbol,  # シンボルを保存
                    'magic': pos.magic  # Magic numberを保存
                }
                print(f"新しいポジションを検出: チケット={ticket}, 方向={self.positions[ticket]['side']}, magic={pos.magic}, エントリー時刻={entry_time}, コメント={pos.comment}")
            else:
                # 既存のポジションのエントリー時刻を更新（MT5から取得した最新情報を使用）
                # プログラム再起動時など、既存ポジションの時刻を確実に保持するため
                if 'entry_time' not in self.positions[ticket] or self.positions[ticket]['entry_time'] is None:
                    self.positions[ticket]['entry_time'] = entry_time
                    print(f"既存ポジションのエントリー時刻を更新: チケット={ticket}, エントリー時刻={entry_time}")
        
        # 決済されたポジションを削除
        active_tickets = {pos.ticket for pos in current_positions}
        closed_tickets = set(self.positions.keys()) - active_tickets
        for ticket in closed_tickets:
            print(f"ポジションが決済されました: チケット={ticket}")
            del self.positions[ticket]
    
    def _check_entry(self, strategy, timeframe):
        """エントリー条件をチェック"""
        # 戦略のシンボルを使用
        symbol = strategy.symbol if hasattr(strategy, 'symbol') else self.symbol
        
        # MT5の接続状態を確認
        if not self.mt5.connected:
            print(f"[警告] MT5の接続が切れています。{strategy.name} ({symbol}) のエントリーチェックをスキップします")
            return
        
        # レートデータを取得
        df = self.mt5.get_rates(symbol, timeframe, count=100)
        if df is None:
            return
        
        # ドンチャン戦略の場合は最小データ数を確認（period + 1）
        min_required = 21  # デフォルト
        if hasattr(strategy, 'period'):
            min_required = strategy.period + 1
        
        if len(df) < min_required:
            return
        
        # エントリー判定
        entry_signal = strategy.should_entry(df)
        
        if entry_signal:
            # 現在価格を取得（前のローソク足がクローズした後の現在価格）
            current_price_info = self.mt5.get_current_price(symbol)
            if current_price_info:
                entry_price = current_price_info['bid'] if entry_signal['side'] == 'sell' else current_price_info['ask']
            else:
                # フォールバック：現在のローソク足の始値を使用
                entry_price = df['open'].iloc[-1]
            
            print(f"\n[{datetime.now()}] エントリーシグナル検出! [{strategy.name}]")
            print(f"  方向: {entry_signal['side']}")
            print(f"  エントリー価格: {entry_price:.5f}")
            print(f"  損切り: {entry_signal['sl']:.5f}")
            if entry_signal.get('tp') is not None:
                print(f"  利確: {entry_signal['tp']:.5f}")
            else:
                print(f"  利確: なし（時間ベース決済）")
            
            # Magic numberを取得
            strategy_magic = getattr(strategy, 'magic', None)
            if strategy_magic is None:
                print(f"  [エラー] 戦略 {strategy.name} にmagic numberが設定されていません")
                return
            
            # ポジション数の制限チェック
            # 1. 全体のポジション数が2つを超えないようにする
            max_total_positions = self.risk_manager.config.get("position_limits", {}).get("max_total_positions", 2)
            if len(self.positions) >= max_total_positions:
                print(f"  [全体] 既に最大ポジション数（{max_total_positions}つ）に達しているため、エントリーをスキップします")
                return
            
            # 2. 同じmagic numberのポジションが既に存在する場合はスキップ
            # 各戦略は1つずつしかポジションを持てない（magic number + symbolで管理）
            if self._has_open_position(symbol, strategy_magic):
                print(f"  [{strategy.name}] 同じmagic number（{strategy_magic}）のポジションが既に存在するため、エントリーをスキップします")
                return
            
            # 戦略に応じたロットサイズを取得
            strategy_lot_size = self._get_lot_size(strategy)
            
            # 3. リスクマネージャーによる総合チェック
            account_info = self.mt5.get_account_info()
            account_balance = account_info.balance if account_info else 0.0
            
            # 日次統計を更新（最新のトレードログから）
            self.risk_manager._update_daily_stats_from_log(self.risk_manager.daily_stats)
            
            can_entry, reasons = self.risk_manager.can_entry(
                positions=self.positions,
                symbol=symbol,
                direction=entry_signal['side'],
                entry_price=entry_price,
                sl=entry_signal.get('sl'),
                lot_size=strategy_lot_size,
                account_balance=account_balance,
                initial_balance=self.initial_balance
            )
            
            if not can_entry:
                print(f"  [リスク管理] エントリーが拒否されました:")
                for reason in reasons:
                    print(f"    - {reason}")
                return
            
            # 注文を送信
            order_type = mt5.ORDER_TYPE_BUY if entry_signal['side'] == 'buy' else mt5.ORDER_TYPE_SELL
            success, ticket, result = self.mt5.place_order(
                symbol=symbol,
                order_type=order_type,
                volume=strategy_lot_size,
                sl=entry_signal['sl'],
                tp=entry_signal['tp'],
                comment=f"{strategy.name} entry",
                magic=strategy_magic
            )
            
            if success:
                print(f"  エントリー成功: チケット={ticket}")
                
                # エントリー時のローソク足の時刻を記録（4時間足の本数カウント用）
                entry_candle_time = None
                if 'time' in df.columns and len(df) > 0:
                    # エントリー時のローソク足（最新のローソク足）の時刻を記録
                    entry_candle_time = pd.to_datetime(df['time'].iloc[-1])
                    print(f"  エントリー時のローソク足時刻: {entry_candle_time}")
                
                # エントリーログを記録
                try:
                    entry_timestamp = datetime.now()
                    if result and hasattr(result, 'time'):
                        entry_timestamp = datetime.fromtimestamp(result.time)
                    
                    entry_log = {
                        'timestamp': entry_timestamp,
                        'strategy': strategy.name,
                        'symbol': symbol,
                        'direction': entry_signal['side'],
                        'entry_price': entry_price,
                        'stop_loss': entry_signal.get('sl'),
                        'take_profit': entry_signal.get('tp'),
                        'volume': strategy_lot_size,
                        'ticket': ticket
                    }
                    self.trade_logger.log_trade(entry_log)
                except Exception as e:
                    print(f"  警告: ログ記録に失敗しました: {e}")
                
                # ポジション情報にエントリー時のローソク足時刻を保存
                # _update_positionsで更新されるが、念のためここでも保存
                if ticket in self.positions:
                    self.positions[ticket]['entry_candle_time'] = entry_candle_time
            else:
                print(f"  エントリー失敗")
    
    def _check_exit(self, strategy, timeframe):
        """エグジット条件をチェック"""
        if len(self.positions) == 0:
            return
        
        # 戦略のシンボルを使用
        symbol = strategy.symbol if hasattr(strategy, 'symbol') else self.symbol
        
        # MT5の接続状態を確認
        if not self.mt5.connected:
            print(f"[警告] MT5の接続が切れています。{strategy.name} ({symbol}) のエグジットチェックをスキップします")
            return
        
        # レートデータを取得
        df = self.mt5.get_rates(symbol, timeframe, count=100)
        if df is None or len(df) < 1:
            return
        
        # Magic numberを取得
        strategy_magic = getattr(strategy, 'magic', None)
        if strategy_magic is None:
            return
        
        # 各ポジションをチェック（magic numberでフィルタリング）
        for ticket, position in list(self.positions.items()):
            # この戦略のmagic numberと一致するポジションのみチェック
            position_magic = position.get('magic')
            if position_magic != strategy_magic:
                continue
            
            # シンボルも一致することを確認
            position_symbol = position.get('symbol')
            if position_symbol != symbol:
                continue
            
            # エントリー時刻が保存されているか確認
            entry_time = position.get('entry_time')
            if entry_time is None:
                print(f"[警告] ポジション {ticket} のエントリー時刻が記録されていません。MT5から再取得します...")
                # MT5から直接ポジション情報を取得してエントリー時刻を更新
                mt5_positions = self.mt5.get_positions(symbol=symbol, magic=strategy_magic)
                for mt5_pos in mt5_positions:
                    if mt5_pos.ticket == ticket:
                        position['entry_time'] = datetime.fromtimestamp(mt5_pos.time)
                        print(f"エントリー時刻を更新: チケット={ticket}, エントリー時刻={position['entry_time']}")
                        break
            
            # エントリー時のローソク足時刻が未設定の場合は、現在のローソク足時刻を設定
            # （プログラム再起動時など、既存ポジションの場合）
            entry_candle_time = position.get('entry_candle_time')
            if entry_candle_time is None and 'time' in df.columns and len(df) > 0:
                # エントリー時刻から最も近いローソク足の時刻を推定
                entry_time_dt = pd.to_datetime(entry_time) if not isinstance(entry_time, pd.Timestamp) else entry_time
                # エントリー時刻以前のローソク足を探す
                df_times = pd.to_datetime(df['time'])
                # エントリー時刻以前の最後のローソク足を探す
                before_entry = df_times[df_times <= entry_time_dt]
                if len(before_entry) > 0:
                    entry_candle_time = before_entry.iloc[-1]
                    position['entry_candle_time'] = entry_candle_time
                    print(f"エントリー時のローソク足時刻を推定: チケット={ticket}, ローソク足時刻={entry_candle_time}")
            
            should_exit = strategy.should_exit(position, df)
                
            if should_exit:
                print(f"\n[{datetime.now()}] エグジットシグナル検出! [{strategy.name}]")
                print(f"  チケット: {ticket}, 方向: {position['side']}, magic: {position_magic}")
                
                # ポジションを決済
                success, profit, balance_after = self.mt5.close_position(ticket)
                if success:
                    print(f"  決済成功: チケット={ticket}, 利益: {profit:.2f}")
                    
                    # リスクマネージャーの統計を更新
                    if profit is not None:
                        self.risk_manager.update_daily_stats(profit)
                    
                    # エグジットログを記録
                    try:
                        exit_timestamp = datetime.now()
                        
                        close_log = {
                            'timestamp': exit_timestamp,
                            'entry_timestamp': position.get('entry_time', exit_timestamp),
                            'strategy': strategy.name,
                            'symbol': position.get('symbol', symbol),
                            'direction': position.get('side'),
                            'entry_price': position.get('entry_price'),
                            'stop_loss': position.get('sl'),
                            'take_profit': position.get('tp'),
                            'volume': position.get('volume'),
                            'ticket': ticket,
                            'profit': profit,
                            'balance_after': balance_after
                        }
                        self.trade_logger.log_close(close_log)
                    except Exception as e:
                        print(f"  警告: ログ記録に失敗しました: {e}")
                else:
                    print(f"  決済失敗: チケット={ticket}")
    
    def get_status(self):
        """現在のステータスを取得"""
        account_info = self.mt5.get_account_info()
        if account_info is None:
            return None
        
        return {
            'balance': account_info.balance,
            'equity': account_info.equity,
            'margin': account_info.margin,
            'free_margin': account_info.margin_free,
            'positions': len(self.positions),
            'positions_detail': self.positions
        }



