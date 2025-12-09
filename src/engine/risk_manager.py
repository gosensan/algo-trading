"""
リスク管理モジュール
システム全体のリスク管理、相関グループ制限、ニュースフィルター
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None


class RiskManager:
    """リスク管理を行うクラス"""
    
    def __init__(self, config_path="config.json"):
        """
        リスクマネージャーを初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.daily_stats = {
            "daily_pnl": 0.0,
            "consecutive_losses": 0,
            "last_reset_date": None,
            "daily_trades": []
        }
    
    def _load_config(self) -> dict:
        """設定ファイルを読み込む"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"警告: 設定ファイルの読み込みに失敗しました: {e}")
                return self._get_default_config()
        else:
            print(f"警告: 設定ファイルが見つかりません: {self.config_path}")
            print("デフォルト設定を使用します")
            return self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """デフォルト設定を返す"""
        return {
            "system": {
                "max_total_risk": 1.5
            },
            "correlation_groups": {
                "JPY": ["USDJPY", "GBPJPY", "CHFJPY", "EURJPY"],
                "USD": ["EURUSD", "GBPUSD", "AUDUSD"]
            },
            "major_news": [
                {
                    "name": "FOMC Rate Decision",
                    "time": "2025-12-17T19:00:00",
                    "block_minutes": 60
                },
                {
                    "name": "NFP",
                    "time": "2025-12-05T13:30:00",
                    "block_minutes": 45
                }
            ],
            "trading_hours": {
                "enabled": True,
                "allowed_hours": [
                    {
                        "day": "monday",
                        "start": "00:00",
                        "end": "23:59"
                    },
                    {
                        "day": "tuesday",
                        "start": "00:00",
                        "end": "23:59"
                    },
                    {
                        "day": "wednesday",
                        "start": "00:00",
                        "end": "23:59"
                    },
                    {
                        "day": "thursday",
                        "start": "00:00",
                        "end": "23:59"
                    },
                    {
                        "day": "friday",
                        "start": "00:00",
                        "end": "23:59"
                    },
                    {
                        "day": "saturday",
                        "start": "00:00",
                        "end": "23:59"
                    },
                    {
                        "day": "sunday",
                        "start": "00:00",
                        "end": "23:59"
                    }
                ]
            },
            "position_limits": {
                "max_positions_per_strategy": 1,
                "max_total_positions": 2
            }
        }
    
    # --- A: システム全体の総リスク管理 ----------------------
    
    def current_total_risk(self) -> float:
        """
        現在の全ポジションのリスク（％）を合計して返す。
        計算式：リスク = (SL距離 / エントリー価格) * ロット * 100
        
        Returns:
            float: 現在の総リスク（％）
        """
        if mt5 is None:
            return 0.0
        
        positions = mt5.positions_get()
        if positions is None:
            return 0.0
        
        total_risk = 0.0
        for p in positions:
            entry = p.price_open
            sl = p.sl
            lot = p.volume
            
            if sl == 0:
                continue  # SLが無いポジションは危険なので取らせないのが理想
            
            risk_pips = abs(entry - sl)
            risk_pct = (risk_pips / entry) * lot * 100
            total_risk += risk_pct
        
        return total_risk
    
    def allowed_to_open(self, new_trade_risk: float) -> bool:
        """
        新規エントリーの前にシステム全体のリスクをチェック。
        
        Args:
            new_trade_risk: 新規トレードのリスク（％）
        
        Returns:
            bool: エントリー可能かどうか
        """
        total = self.current_total_risk()
        max_risk = self.config.get("system", {}).get("max_total_risk", 1.5)
        
        if total + new_trade_risk > max_risk:
            print(f"[RiskManager] 総リスクオーバー: {total + new_trade_risk:.2f}% > {max_risk}%")
            return False
        
        return True
    
    def _calculate_trade_risk(self, entry_price: float, sl: float, lot_size: float) -> float:
        """
        新規トレードのリスク（％）を計算
        
        Args:
            entry_price: エントリー価格
            sl: 損切り価格
            lot_size: ロットサイズ
        
        Returns:
            float: リスク（％）
        """
        if entry_price == 0 or sl == 0:
            return 0.0
        
        risk_pips = abs(entry_price - sl)
        risk_pct = (risk_pips / entry_price) * lot_size * 100
        return risk_pct
    
    # --- B: 相関グループの同方向制限 --------------------------
    
    def correlated_pair_block(self, symbol: str, direction: str) -> bool:
        """
        symbol が属する相関グループを確認し、
        同方向のポジションが既にあればブロック。
        
        Args:
            symbol: シンボル
            direction: 方向（'buy' or 'sell'）
        
        Returns:
            bool: True=許可, False=ブロック
        """
        if mt5 is None:
            return True
        
        groups = self.config.get("correlation_groups", {})
        target_group = None
        
        for group_name, pairs in groups.items():
            if symbol in pairs:
                target_group = pairs
                break
        
        if not target_group:
            return True  # 相関グループに属してない → OK
        
        positions = mt5.positions_get()
        if positions is None:
            return True
        
        for p in positions:
            if p.symbol in target_group:
                # mt5.ORDER_TYPE_BUY = 0, mt5.ORDER_TYPE_SELL = 1
                p_direction = "buy" if p.type == 0 else "sell"
                if (p.type == 0 and direction == "buy") or (p.type == 1 and direction == "sell"):
                    print(f"[RiskManager] 相関ペア同方向ブロック: {p.symbol} 既に保有中")
                    return False
        
        return True
    
    # --- C: 極端ニュースフィルター ------------------------------
    
    def news_block(self) -> bool:
        """
        極端ニュースの予定を config に書いておき、
        その前後は取引停止。
        
        Returns:
            bool: True=許可, False=ブロック
        """
        now = datetime.now()
        
        major_news = self.config.get("major_news", [])
        for event in major_news:
            try:
                event_time = datetime.fromisoformat(event["time"])
                window_minutes = event.get("block_minutes", 60)
                
                # イベント時刻の前後window_minutes分をブロック
                time_diff_seconds = abs((event_time - now).total_seconds())
                if time_diff_seconds <= window_minutes * 60:
                    print(f"[RiskManager] 重大イベントブロック中: {event['name']}")
                    return False
            except (ValueError, KeyError) as e:
                print(f"警告: ニュースイベントの解析に失敗: {e}")
                continue
        
        return True
    
    # --- 既存コードとの互換性のためのメソッド ------------------
    
    def check_trading_hours(self) -> Tuple[bool, str]:
        """
        取引時間帯をチェック（既存コードとの互換性のため）
        
        Returns:
            tuple: (許可可否, 理由メッセージ)
        """
        if not self.config.get("trading_hours", {}).get("enabled", False):
            return True, ""
        
        now = datetime.now()
        current_day = now.strftime("%A").lower()
        current_time = now.strftime("%H:%M")
        
        allowed_hours = self.config.get("trading_hours", {}).get("allowed_hours", [])
        
        for hour_config in allowed_hours:
            if hour_config.get("day", "").lower() == current_day:
                start_time = hour_config.get("start", "00:00")
                end_time = hour_config.get("end", "23:59")
                
                if start_time <= current_time <= end_time:
                    return True, ""
        
        return False, f"取引時間外です（現在: {current_day} {current_time}）"
    
    def can_entry(self, positions: dict, symbol: str, direction: str,
                  entry_price: float, sl: float, lot_size: float,
                  account_balance: float, initial_balance: float = None) -> Tuple[bool, List[str]]:
        """
        エントリー可能かどうかを総合的にチェック（既存コードとの互換性のため）
        
        Args:
            positions: 現在のポジション辞書
            symbol: 新規エントリーのシンボル
            direction: 新規エントリーの方向
            entry_price: エントリー価格
            sl: 損切り価格
            lot_size: ロットサイズ
            account_balance: 現在のアカウント残高
            initial_balance: 日初のアカウント残高（未使用）
        
        Returns:
            tuple: (許可可否, 理由メッセージのリスト)
        """
        reasons = []
        
        # 1. 取引時間帯チェック
        can_trade, msg = self.check_trading_hours()
        if not can_trade:
            reasons.append(msg)
            return False, reasons
        
        # 2. ニュースブロックチェック
        if not self.news_block():
            reasons.append("重大イベントブロック中")
            return False, reasons
        
        # 3. 相関ペアブロックチェック
        if not self.correlated_pair_block(symbol, direction):
            reasons.append(f"相関ペア同方向ブロック: {symbol}")
            return False, reasons
        
        # 4. システム全体のリスクチェック
        new_trade_risk = self._calculate_trade_risk(entry_price, sl, lot_size)
        if not self.allowed_to_open(new_trade_risk):
            reasons.append(f"総リスクオーバー: {self.current_total_risk() + new_trade_risk:.2f}%")
            return False, reasons
        
        return True, reasons
    
    def update_daily_stats(self, profit: float):
        """
        日次統計を更新（決済時に呼び出す）
        
        Args:
            profit: 決済時の利益
        """
        self.daily_stats["daily_pnl"] += profit
        
        if profit < 0:
            self.daily_stats["consecutive_losses"] += 1
        else:
            self.daily_stats["consecutive_losses"] = 0
    
    def _update_daily_stats_from_log(self, stats: dict):
        """
        トレードログから日次統計を更新（既存コードとの互換性のため）
        
        Args:
            stats: 統計辞書（更新される）
        """
        # 簡易実装: 実際のログファイルから読み込む場合はここを実装
        # 現在は空の実装（既存のdaily_statsを使用）
        pass
