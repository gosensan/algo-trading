"""
トレード実行エンジン
"""
import time
from datetime import datetime
from .mt5_connector import MT5Connector

try:
    import MetaTrader5 as mt5
except ImportError:
    print("エラー: MetaTrader5モジュールが見つかりません。")
    mt5 = None


class TradeExecutor:
    """トレードの実行を管理するクラス"""
    
    def __init__(self, strategy, mt5_connector, symbol="EURUSD", lot_size=0.01):
        """
        トレード実行エンジンを初期化
        
        Args:
            strategy: 使用する戦略（BollingerStrategyなど）
            mt5_connector: MT5Connectorインスタンス
            symbol: 取引する通貨ペア
            lot_size: ロットサイズ
        """
        self.strategy = strategy
        self.mt5 = mt5_connector
        self.symbol = symbol
        self.lot_size = lot_size
        self.positions = {}  # ポジション管理: {ticket: position_info}
    
    def run(self, timeframe=None, check_interval=60):
        """
        戦略を実行（継続的に監視）
        
        Args:
            timeframe: 時間足（Noneの場合はH1）
            check_interval: チェック間隔（秒）
        """
        if mt5 is None:
            print("エラー: MetaTrader5モジュールが利用できません。")
            return
        
        if timeframe is None:
            timeframe = mt5.TIMEFRAME_H1
        
        print(f"戦略を開始します: {self.strategy.name}")
        print(f"シンボル: {self.symbol}, ロットサイズ: {self.lot_size}")
        print(f"チェック間隔: {check_interval}秒")
        print("-" * 60)
        
        try:
            while True:
                # 現在のポジションを更新
                self._update_positions()
                
                # エントリー判定
                self._check_entry(timeframe)
                
                # エグジット判定
                self._check_exit(timeframe)
                
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
        current_positions = self.mt5.get_positions(self.symbol)
        
        # 既存のポジションを更新
        for pos in current_positions:
            ticket = pos.ticket
            if ticket not in self.positions:
                # 新しいポジション
                self.positions[ticket] = {
                    'ticket': ticket,
                    'side': 'buy' if pos.type == mt5.ORDER_TYPE_BUY else 'sell',
                    'entry_price': pos.price_open,
                    'entry_time': datetime.fromtimestamp(pos.time),
                    'volume': pos.volume,
                    'sl': pos.sl,
                    'tp': pos.tp
                }
                print(f"新しいポジションを検出: チケット={ticket}, 方向={self.positions[ticket]['side']}")
        
        # 決済されたポジションを削除
        active_tickets = {pos.ticket for pos in current_positions}
        closed_tickets = set(self.positions.keys()) - active_tickets
        for ticket in closed_tickets:
            print(f"ポジションが決済されました: チケット={ticket}")
            del self.positions[ticket]
    
    def _check_entry(self, timeframe):
        """エントリー条件をチェック"""
        # レートデータを取得
        df = self.mt5.get_rates(self.symbol, timeframe, count=100)
        if df is None or len(df) < 21:
            return
        
        # エントリー判定
        entry_signal = self.strategy.should_entry(df)
        
        if entry_signal:
            # 現在価格を取得（前のローソク足がクローズした後の現在価格）
            current_price_info = self.mt5.get_current_price(self.symbol)
            if current_price_info:
                entry_price = current_price_info['bid'] if entry_signal['side'] == 'sell' else current_price_info['ask']
            else:
                # フォールバック：現在のローソク足の始値を使用
                entry_price = df['open'].iloc[-1]
            
            print(f"\n[{datetime.now()}] エントリーシグナル検出!")
            print(f"  方向: {entry_signal['side']}")
            print(f"  エントリー価格: {entry_price:.5f}")
            print(f"  損切り: {entry_signal['sl']:.5f}")
            print(f"  利確: {entry_signal['tp']:.5f}")
            
            # 既にポジションを持っている場合はスキップ
            if len(self.positions) > 0:
                print("  既にポジションがあるため、エントリーをスキップします")
                return
            
            # 注文を送信
            order_type = mt5.ORDER_TYPE_BUY if entry_signal['side'] == 'buy' else mt5.ORDER_TYPE_SELL
            success, ticket = self.mt5.place_order(
                symbol=self.symbol,
                order_type=order_type,
                volume=self.lot_size,
                sl=entry_signal['sl'],
                tp=entry_signal['tp'],
                comment=f"{self.strategy.name} entry"
            )
            
            if success:
                print(f"  エントリー成功: チケット={ticket}")
            else:
                print(f"  エントリー失敗")
    
    def _check_exit(self, timeframe):
        """エグジット条件をチェック"""
        if len(self.positions) == 0:
            return
        
        # レートデータを取得
        df = self.mt5.get_rates(self.symbol, timeframe, count=100)
        if df is None or len(df) < 1:
            return
        
        # 各ポジションをチェック
        for ticket, position in list(self.positions.items()):
            should_exit = self.strategy.should_exit(position, df)
            
            if should_exit:
                print(f"\n[{datetime.now()}] エグジットシグナル検出!")
                print(f"  チケット: {ticket}, 方向: {position['side']}")
                
                # ポジションを決済
                success = self.mt5.close_position(ticket)
                if success:
                    print(f"  決済成功: チケット={ticket}")
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



