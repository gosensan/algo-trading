"""
ドンチャンブレイクアウト戦略
4時間足10期間のドンチャンラインを実線が突破してクローズした時のみエントリー
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class DonchianStrategy:
    def __init__(self, symbol="EURUSD", period=10):
        """
        ドンチャンブレイクアウト戦略を初期化
        
        Args:
            symbol: 通貨ペア
            period: ドンチャン期間（デフォルト: 10）
        """
        self.symbol = symbol
        self.name = "donchian_breakout"
        self.magic = 2001  # ドンチャンブレイクアウト戦略のmagic number
        self.period = period
        self.last_entry_date = None  # 1日1回制限のため
    
    def _calculate_donchian_channels(self, df, period=None):
        """
        ドンチャンチャネルを計算
        
        Args:
            df: 価格データ（DataFrame）
            period: 期間（Noneの場合はself.periodを使用）
        
        Returns:
            tuple: (upper_band, lower_band) または (None, None)
        """
        if period is None:
            period = self.period
        
        if len(df) < period:
            print(f"Donchian channels: insufficient data (len={len(df)}, period={period})")
            return None, None
        
        # highとlowの存在確認
        if 'high' not in df.columns:
            print(f"ERROR: 'high' column missing! Available columns: {df.columns.tolist()}")
            return None, None
        
        if 'low' not in df.columns:
            print(f"ERROR: 'low' column missing! Available columns: {df.columns.tolist()}")
            return None, None
        
        # 上限: 過去N期間の最高値
        upper_band = df['high'].rolling(window=period).max()
        
        # 下限: 過去N期間の最低値
        lower_band = df['low'].rolling(window=period).min()
        
        # デバッグ: 計算結果の確認
        if upper_band.isna().all() or lower_band.isna().all():
            print(f"ERROR: Donchian channels calculation failed (all NaN)")
            return None, None
        
        return upper_band, lower_band
    
    def should_entry(self, df):
        """
        エントリー条件を満たすか判定
        実線（close）がドンチャンラインを突破してクローズした時のみエントリー
        
        Args:
            df: 価格データ（DataFrame）
        
        Returns:
            dict: エントリーシグナル情報 または None
        """
        if df is None or len(df) < self.period + 1:
            return None
        
        # --- debug 出力（テスト時だけ有効に） ---
        print("Donchian debug len:", len(df))
        print("Donchian debug columns:", df.columns.tolist())
        print("Donchian debug df head:")
        print(df[['time', 'open', 'high', 'low', 'close']].head() if all(col in df.columns for col in ['time', 'open', 'high', 'low', 'close']) else df.head())
        print("last times:", df['time'].iloc[-3:].tolist())
        print("last closes:", df['close'].iloc[-3:].tolist())
        
        # highとlowの存在確認
        if 'high' not in df.columns or 'low' not in df.columns:
            print(f"ERROR: 'high' or 'low' column missing! Available columns: {df.columns.tolist()}")
            return None
        
        upper_band, lower_band = self._calculate_donchian_channels(df)
        if upper_band is None or lower_band is None:
            print("ERROR: Failed to calculate donchian channels")
            return None
        
        # 前の足（-2）と現在足（-1）
        prev_close = df['close'].iloc[-2]
        prev_high = df['high'].iloc[-2]
        prev_low = df['low'].iloc[-2]
        prev_upper = upper_band.iloc[-2]
        prev_lower = lower_band.iloc[-2]
        current_close = df['close'].iloc[-1]
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        
        # --- 許容誤差をシンボルの point ベースにする ---
        try:
            import MetaTrader5 as mt5
            info = mt5.symbol_info(self.symbol)
            if info is not None and hasattr(info, 'point') and info.point > 0:
                point = info.point
            else:
                # シンボル名から推測
                if 'JPY' in self.symbol:
                    point = 0.001  # JPYペアは0.001
                elif 'XAU' in self.symbol or 'GOLD' in self.symbol:
                    point = 0.01  # ゴールドは0.01
                else:
                    point = 0.00001  # その他の通貨ペアは0.00001
        except Exception as e:
            # シンボル名から推測
            if 'JPY' in self.symbol:
                point = 0.001  # JPYペアは0.001
            elif 'XAU' in self.symbol or 'GOLD' in self.symbol:
                point = 0.01  # ゴールドは0.01
            else:
                point = 0.00001  # その他の通貨ペアは0.00001
        
        tol = point * 0.5  # 誤差許容（0.5ティック分）
        
        # デバッグ出力: point値と許容誤差を表示
        print(f"Donchian debug symbol: {self.symbol}, point: {point}, tolerance: {tol}")
        print(f"prev_high: {prev_high}, prev_low: {prev_low}, prev_close: {prev_close}")
        print(f"prev_upper: {prev_upper}, prev_lower: {prev_lower}")
        
        side = None
        # 前のローソク足のhighが上限を超えていたらロング（突破確認）
        # 許容誤差を考慮: prev_high >= prev_upper - tol でもOK
        if prev_high >= prev_upper - tol:
            side = "buy"
            print(f"Donchian BUY signal: prev_high({prev_high}) >= prev_upper({prev_upper}) - tol({tol})")
        # 前のローソク足のlowが下限を下回っていたらショート（突破確認）
        # 許容誤差を考慮: prev_low <= prev_lower + tol でもOK
        elif prev_low <= prev_lower + tol:
            side = "sell"
            print(f"Donchian SELL signal: prev_low({prev_low}) <= prev_lower({prev_lower}) + tol({tol})")
        
        if side is None:
            print(f"Donchian no signal: prev_high({prev_high}) not >= prev_upper({prev_upper}) - tol({tol}) and prev_low({prev_low}) not <= prev_lower({prev_lower}) + tol({tol})")
            return None
        
        # SLは反対のドンチャンライン（currentではなくprevを使う選択肢もあり）
        if side == "buy":
            sl = float(prev_lower)
        else:
            sl = float(prev_upper)
        
        tp = None
        
        # （テスト中は日付制限をしない。運用時はここを入れる）
        # self.last_entry_date = current_date
        
        return {
            "side": side,
            "sl": sl,
            "tp": tp
        }
    
    def should_exit(self, position, df):
        """
        決済条件を満たすか判定
        4時間足12本クローズで決済
        
        Args:
            position: ポジション情報（dict）
            df: 価格データ（DataFrame）
        
        Returns:
            bool: 決済すべきかどうか
        """
        if position is None or df is None or len(df) < 1:
            return False
        
        # エントリー時のローソク足時刻を取得
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
        
        # エントリー時のローソク足時刻が取得できた場合、4時間足12本経過をチェック
        if entry_candle_time is not None and 'time' in df.columns:
            # 現在のローソク足の時刻を取得（最新のローソク足）
            current_candle_time = pd.to_datetime(df['time'].iloc[-1])
            
            # エントリー時のローソク足から現在のローソク足までの本数を計算
            # 4時間足なので、時刻の差分から本数を計算
            time_diff = current_candle_time - entry_candle_time
            # 4時間 = 4 * 60 * 60 = 14400秒
            candles_elapsed = int(time_diff.total_seconds() / 14400)
            
            # デバッグ情報を出力
            print(f"[Donchian] ローソク足経過チェック: エントリー時のローソク足={entry_candle_time}, 現在のローソク足={current_candle_time}, 経過本数={candles_elapsed}本")
            
            # 12本経過で決済
            if candles_elapsed >= 12:
                print(f"[Donchian] 4時間足12本経過により決済: 経過本数={candles_elapsed}本")
                return True
        
        # 利食い設定はなしなので、12本経過のみで決済
        return False





