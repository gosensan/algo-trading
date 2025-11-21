"""
ボリンジャーバンド戦略
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class BollingerStrategy:
    def __init__(self, symbol="EURUSD"):
        self.symbol = symbol
        self.name = "bollinger"
        self.last_entry_date = None  # 1日1回制限のため
        
    def _calculate_bollinger_bands(self, df, period=20, num_std=2):
        """ボリンジャーバンドを計算"""
        if len(df) < period:
            return None, None, None
        
        # 移動平均（中央線）
        sma = df['close'].rolling(window=period).mean()
        
        # 標準偏差
        std = df['close'].rolling(window=period).std()
        
        # 上限（+2σ）と下限（-2σ）
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        
        return upper_band, sma, lower_band
    
    def _calculate_atr(self, df, period=14):
        """ATR（Average True Range）を計算"""
        if len(df) < period + 1:
            return None
        
        high = df['high']
        low = df['low']
        close = df['close']
        
        # True Rangeの計算
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # ATR（期間の平均）
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def should_entry(self, df):
        """エントリー条件を満たすか判定"""
        if df is None or len(df) < 21:  # ボリンジャーバンド20期間 + ATR14期間 + 前の足
            return None
        
        # 現在の日付を取得（1日1回制限のため）
        if 'time' in df.columns:
            current_date = pd.to_datetime(df['time'].iloc[-1]).date()
        else:
            current_date = datetime.now().date()
        
        # 1日1回制限チェック
        if self.last_entry_date == current_date:
            return None
        
        # ボリンジャーバンドを計算
        upper_band, middle_band, lower_band = self._calculate_bollinger_bands(df)
        
        if upper_band is None or middle_band is None or lower_band is None:
            return None
        
        # 前の足（インデックス-2）と現在の足（インデックス-1）を取得
        if len(df) < 2:
            return None
        
        # 前のローソク足（-2）がクローズしたことを確認
        # 5分足の場合、前のローソク足の時刻から5分以上経過している必要がある
        if 'time' in df.columns:
            prev_candle_time = pd.to_datetime(df['time'].iloc[-2])
            current_candle_time = pd.to_datetime(df['time'].iloc[-1])
            current_time = pd.Timestamp.now()
            
            # 前のローソク足がクローズしたことを確認
            # 現在のローソク足の時刻が前のローソク足の時刻 + 5分以上経過している必要がある
            time_diff = (current_candle_time - prev_candle_time).total_seconds()
            if time_diff < 300:  # 5分 = 300秒
                # 前のローソク足がまだクローズしていない可能性がある
                return None
            
            # 現在のローソク足が新しいローソク足であることを確認
            # 現在時刻が現在のローソク足の時刻 + 5分未満の場合、まだ形成中
            current_candle_age = (current_time - current_candle_time).total_seconds()
            if current_candle_age < 60:  # 現在のローソク足が形成されてから1分未満の場合は待つ
                return None
        
        # 前のローソク足（-2）のデータを取得
        prev_close = df['close'].iloc[-2]
        prev_open = df['open'].iloc[-2]
        prev_upper = upper_band.iloc[-2]
        prev_lower = lower_band.iloc[-2]
        
        # エントリー条件チェック
        # 前のローソク足（-2）がボリンジャーバンドの外側から内側に戻ったことを確認
        side = None
        
        # 上外→内：前のローソク足の始値が上限を超えていて、終値が上限以下でクローズ
        # （前のローソク足が上限を超えた状態から、上限以下でクローズした）
        if prev_open > prev_upper and prev_close <= prev_upper:
            side = "sell"  # ショート
        
        # 下外→内：前のローソク足の始値が下限を下回っていて、終値が下限以上でクローズ
        # （前のローソク足が下限を下回った状態から、下限以上でクローズした）
        elif prev_open < prev_lower and prev_close >= prev_lower:
            side = "buy"  # ロング
        
        if side is None:
            return None
        
        # ATRを計算して損切りを設定
        atr = self._calculate_atr(df, period=14)
        if atr is None or pd.isna(atr.iloc[-1]):
            return None
        
        current_atr = atr.iloc[-1]
        current_price = df['close'].iloc[-1]
        
        # 損切り：ATRの3倍
        current_middle = middle_band.iloc[-1]
        if side == "buy":
            sl = current_price - (current_atr * 3)
            tp = float(current_middle)  # 利確は中央線（should_exitでも判定）
        else:  # sell
            sl = current_price + (current_atr * 3)
            tp = float(current_middle)  # 利確は中央線（should_exitでも判定）
        
        # エントリー日を記録
        self.last_entry_date = current_date
        
        return {
            "side": side,
            "sl": float(sl),
            "tp": tp
        }
    
    def should_exit(self, position, df):
        """決済条件を満たすか判定"""
        if position is None or df is None or len(df) < 1:
            return False
        
        # エントリー時刻を取得（72時間後の強制決済のため）
        entry_time = None
        if hasattr(position, 'entry_time'):
            entry_time = position.entry_time
        elif isinstance(position, dict) and 'entry_time' in position:
            entry_time = position['entry_time']
        
        # 72時間後の強制決済チェック
        if entry_time:
            if isinstance(entry_time, str):
                entry_time = pd.to_datetime(entry_time)
            elif isinstance(entry_time, pd.Timestamp):
                pass
            else:
                entry_time = pd.to_datetime(entry_time)
            
            current_time = None
            if 'time' in df.columns:
                current_time = pd.to_datetime(df['time'].iloc[-1])
            else:
                current_time = pd.Timestamp.now()
            
            if current_time - entry_time >= timedelta(hours=72):
                return True
        
        # ボリンジャーバンドの中央線を取得
        upper_band, middle_band, lower_band = self._calculate_bollinger_bands(df)
        if middle_band is None or len(middle_band) == 0:
            return False
        
        current_close = df['close'].iloc[-1]
        current_middle = middle_band.iloc[-1]
        
        # ポジションの方向を取得
        side = None
        if hasattr(position, 'side'):
            side = position.side
        elif isinstance(position, dict) and 'side' in position:
            side = position['side']
        
        if side is None:
            return False
        
        # 利確条件：終値がボリンジャーバンドの中央線を超えてクローズ
        # ロングの場合：終値が中央線を上回る
        # ショートの場合：終値が中央線を下回る
        if side == "buy":
            if current_close > current_middle:
                return True
        elif side == "sell":
            if current_close < current_middle:
                return True
        
        return False
