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
        self.magic = 1001  # ボリンジャーバンド戦略のmagic number
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
        
        # 前のローソク足（-2）のデータを取得
        prev_close = df['close'].iloc[-2]
        prev_open = df['open'].iloc[-2]
        prev_high = df['high'].iloc[-2]
        prev_low = df['low'].iloc[-2]
        prev_upper = upper_band.iloc[-2]
        prev_lower = lower_band.iloc[-2]
        
        # エントリー条件チェック
        # 前のローソク足（-2）がボリンジャーバンドの外側から内側に戻ったことを確認
        side = None
        
        # 上外→内：前のローソク足が上限を超えていた（highが上限を超えている）が、
        # 終値が上限以下でクローズした
        # （より柔軟な条件：highが上限を超えていて、closeが上限以下）
        if prev_high > prev_upper and prev_close <= prev_upper:
            side = "sell"  # ショート
            print(f"[Bollinger] ショートエントリー条件検出:")
            print(f"  prev_high: {prev_high:.5f} > prev_upper: {prev_upper:.5f}")
            print(f"  prev_close: {prev_close:.5f} <= prev_upper: {prev_upper:.5f}")
        
        # 下外→内：前のローソク足が下限を下回っていた（lowが下限を下回っている）が、
        # 終値が下限以上でクローズした
        # （より柔軟な条件：lowが下限を下回っていて、closeが下限以上）
        elif prev_low < prev_lower and prev_close >= prev_lower:
            side = "buy"  # ロング
            print(f"[Bollinger] ロングエントリー条件検出:")
            print(f"  prev_low: {prev_low:.5f} < prev_lower: {prev_lower:.5f}")
            print(f"  prev_close: {prev_close:.5f} >= prev_lower: {prev_lower:.5f}")
        
        if side is None:
            # デバッグ情報を出力
            print(f"[Bollinger] エントリー条件を満たしていません:")
            print(f"  prev_high: {prev_high:.5f}, prev_upper: {prev_upper:.5f}")
            print(f"  prev_low: {prev_low:.5f}, prev_lower: {prev_lower:.5f}")
            print(f"  prev_close: {prev_close:.5f}")
            print(f"  上外→内条件: prev_high > prev_upper and prev_close <= prev_upper")
            print(f"    → {prev_high > prev_upper} and {prev_close <= prev_upper} = {prev_high > prev_upper and prev_close <= prev_upper}")
            print(f"  下外→内条件: prev_low < prev_lower and prev_close >= prev_lower")
            print(f"    → {prev_low < prev_lower} and {prev_close >= prev_lower} = {prev_low < prev_lower and prev_close >= prev_lower}")
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
        
        # まず、ボリンジャーバンドの中央線到達で決済するかチェック
        # （中央線到達の場合は、ローソク足の本数に関係なく決済）
        
        # ボリンジャーバンドの中央線を取得
        upper_band, middle_band, lower_band = self._calculate_bollinger_bands(df)
        if middle_band is None or len(middle_band) == 0:
            # 中央線が計算できない場合は、ローソク足の本数チェックに進む
            pass
        else:
            current_close = df['close'].iloc[-1]
            current_middle = middle_band.iloc[-1]
            
            # ポジションの方向を取得
            side = None
            if hasattr(position, 'side'):
                side = position.side
            elif isinstance(position, dict) and 'side' in position:
                side = position['side']
            
            if side is not None:
                # 利確条件：終値がボリンジャーバンドの中央線を超えてクローズ
                # ロングの場合：終値が中央線を上回る
                # ショートの場合：終値が中央線を下回る
                if side == "buy":
                    if current_close > current_middle:
                        print(f"[Bollinger] 中央線到達により決済: 終値={current_close:.5f}, 中央線={current_middle:.5f}")
                        return True
                elif side == "sell":
                    if current_close < current_middle:
                        print(f"[Bollinger] 中央線到達により決済: 終値={current_close:.5f}, 中央線={current_middle:.5f}")
                        return True
        
        # 中央線到達がなかった場合、4時間足18本経過で決済
        entry_candle_time = None
        if isinstance(position, dict) and 'entry_candle_time' in position:
            entry_candle_time = position['entry_candle_time']
        
        # エントリー時のローソク足時刻が記録されていない場合は、エントリー時刻から推定
        if entry_candle_time is None:
            entry_time = None
            if isinstance(position, dict) and 'entry_time' in position:
                entry_time = position['entry_time']
            
            if entry_time:
                # エントリー時刻をdatetimeに変換
                if isinstance(entry_time, str):
                    entry_time = pd.to_datetime(entry_time)
                elif isinstance(entry_time, pd.Timestamp):
                    pass
                elif isinstance(entry_time, datetime):
                    entry_time = pd.to_datetime(entry_time)
                else:
                    entry_time = pd.to_datetime(entry_time)
                
                # エントリー時刻以前の最後のローソク足を探す
                if 'time' in df.columns:
                    df_times = pd.to_datetime(df['time'])
                    before_entry = df_times[df_times <= entry_time]
                    if len(before_entry) > 0:
                        entry_candle_time = before_entry.iloc[-1]
        
        # エントリー時のローソク足時刻が取得できた場合、4時間足18本経過をチェック
        if entry_candle_time is not None and 'time' in df.columns:
            # 現在のローソク足の時刻を取得（最新のローソク足）
            current_candle_time = pd.to_datetime(df['time'].iloc[-1])
            
            # エントリー時のローソク足から現在のローソク足までの本数を計算
            # 4時間足なので、時刻の差分から本数を計算
            time_diff = current_candle_time - entry_candle_time
            # 4時間 = 4 * 60 * 60 = 14400秒
            candles_elapsed = int(time_diff.total_seconds() / 14400)
            
            # デバッグ情報を出力
            print(f"[Bollinger] ローソク足経過チェック: エントリー時のローソク足={entry_candle_time}, 現在のローソク足={current_candle_time}, 経過本数={candles_elapsed}本")
            
            # 18本経過で決済
            if candles_elapsed >= 18:
                print(f"[Bollinger] 4時間足18本経過により決済: 経過本数={candles_elapsed}本")
                return True
        
        return False
