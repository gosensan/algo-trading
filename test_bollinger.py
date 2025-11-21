"""
ボリンジャーバンド戦略の稼働テスト
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.strategies.bollinger import BollingerStrategy


def generate_sample_data(num_candles=50, base_price=1.1000, trigger_entry=False):
    """テスト用のサンプルデータを生成
    
    Args:
        num_candles: ローソク足の数
        base_price: 基準価格
        trigger_entry: Trueの場合、エントリー条件を満たすデータを生成
    """
    np.random.seed(42)
    
    # 時間データを生成
    start_time = datetime.now() - timedelta(days=num_candles)
    times = [start_time + timedelta(hours=i) for i in range(num_candles)]
    
    if trigger_entry:
        # エントリー条件を満たすデータを生成
        # まず、通常のデータを生成
        prices = [base_price]
        for i in range(1, num_candles):
            change = np.random.normal(0, 0.001)
            prices.append(prices[-1] + change)
        
        # データフレームを作成
        df_temp = pd.DataFrame({
            'time': times[:len(prices)],
            'close': prices
        })
        
        # ボリンジャーバンドを計算
        upper, middle, lower = BollingerStrategy()._calculate_bollinger_bands(df_temp)
        
        if upper is not None and len(df_temp) >= 22:
            # 前の足（インデックス-2）のボリンジャーバンドを取得
            prev_upper = upper.iloc[-2]
            prev_lower = lower.iloc[-2]
            
            # 前の足を上限より上に設定
            df_temp.loc[df_temp.index[-2], 'close'] = prev_upper + 0.002
            
            # ボリンジャーバンドを再計算
            upper_new, middle_new, lower_new = BollingerStrategy()._calculate_bollinger_bands(df_temp)
            current_upper = upper_new.iloc[-1]
            
            # 現在の足を上限以下に設定
            df_temp.loc[df_temp.index[-1], 'close'] = current_upper - 0.001
            
            # OHLCデータを生成
            prices = df_temp['close'].tolist()
        else:
            # フォールバック: シンプルなアプローチ
            prices = [base_price]
            for i in range(1, num_candles):
                change = np.random.normal(0, 0.001)
                prices.append(prices[-1] + change)
    else:
        # 価格データを生成（ランダムウォーク）
        prices = [base_price]
        for i in range(1, num_candles):
            change = np.random.normal(0, 0.001)  # 小さなランダム変動
            prices.append(prices[-1] + change)
    
    # OHLCデータを生成
    data = []
    for i, (time, close) in enumerate(zip(times, prices)):
        high = close + abs(np.random.normal(0, 0.0005))
        low = close - abs(np.random.normal(0, 0.0005))
        open_price = prices[i-1] if i > 0 else close
        
        data.append({
            'time': time,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close
        })
    
    return pd.DataFrame(data)


def test_entry_conditions():
    """エントリー条件のテスト"""
    print("=" * 60)
    print("エントリー条件のテスト")
    print("=" * 60)
    
    strategy = BollingerStrategy(symbol="EURUSD")
    
    # まず通常のデータでテスト
    print("\n--- 通常のデータでのテスト ---")
    df = generate_sample_data(num_candles=50)
    
    print(f"\n生成されたデータ: {len(df)}本のローソク足")
    print(f"期間: {df['time'].iloc[0]} ～ {df['time'].iloc[-1]}")
    print(f"\n最新5本の価格:")
    print(df[['time', 'close']].tail(5).to_string(index=False))
    
    # エントリー判定
    result = strategy.should_entry(df)
    
    if result:
        print(f"\n[OK] エントリーシグナル検出!")
        print(f"  方向: {result['side']}")
        print(f"  エントリー価格: {df['close'].iloc[-1]:.5f}")
        print(f"  損切り(SL): {result['sl']:.5f}")
        print(f"  利確(TP): {result['tp']:.5f}")
    else:
        print(f"\n[NG] エントリー条件を満たしていません")
        print("  （ボリンジャーバンドの外→内への動きが検出されませんでした）")
    
    # エントリー条件を満たすデータでテスト
    print("\n--- エントリー条件を満たすデータでのテスト ---")
    df_trigger = generate_sample_data(num_candles=50, trigger_entry=True)
    print(f"\n生成されたデータ: {len(df_trigger)}本のローソク足")
    print(f"期間: {df_trigger['time'].iloc[0]} ～ {df_trigger['time'].iloc[-1]}")
    print(f"\n最新5本の価格:")
    print(df_trigger[['time', 'close']].tail(5).to_string(index=False))
    
    # ボリンジャーバンドを計算して表示
    upper, middle, lower = strategy._calculate_bollinger_bands(df_trigger)
    if upper is not None:
        print(f"\nボリンジャーバンド（最新）:")
        print(f"  上限: {upper.iloc[-1]:.5f}")
        print(f"  中央: {middle.iloc[-1]:.5f}")
        print(f"  下限: {lower.iloc[-1]:.5f}")
        print(f"  現在価格: {df_trigger['close'].iloc[-1]:.5f}")
        print(f"  前の価格: {df_trigger['close'].iloc[-2]:.5f}")
    
    # デバッグ: 実際の条件を確認
    upper_actual, middle_actual, lower_actual = strategy._calculate_bollinger_bands(df_trigger)
    if upper_actual is not None and len(df_trigger) >= 2:
        prev_close_actual = df_trigger['close'].iloc[-2]
        current_close_actual = df_trigger['close'].iloc[-1]
        prev_upper_actual = upper_actual.iloc[-2]
        prev_lower_actual = lower_actual.iloc[-2]
        current_upper_actual = upper_actual.iloc[-1]
        current_lower_actual = lower_actual.iloc[-1]
        
        print(f"\nデバッグ情報:")
        print(f"  前の足の終値: {prev_close_actual:.5f}")
        print(f"  前の足の上限: {prev_upper_actual:.5f}")
        print(f"  前の足の下限: {prev_lower_actual:.5f}")
        print(f"  現在の足の終値: {current_close_actual:.5f}")
        print(f"  現在の足の上限: {current_upper_actual:.5f}")
        print(f"  現在の足の下限: {current_lower_actual:.5f}")
        print(f"  条件1 (上外→内): {prev_close_actual:.5f} > {prev_upper_actual:.5f} = {prev_close_actual > prev_upper_actual}")
        print(f"  条件2 (上外→内): {current_close_actual:.5f} <= {current_upper_actual:.5f} = {current_close_actual <= current_upper_actual}")
        print(f"  条件3 (下外→内): {prev_close_actual:.5f} < {prev_lower_actual:.5f} = {prev_close_actual < prev_lower_actual}")
        print(f"  条件4 (下外→内): {current_close_actual:.5f} >= {current_lower_actual:.5f} = {current_close_actual >= current_lower_actual}")
    
    result_trigger = strategy.should_entry(df_trigger)
    
    if result_trigger:
        print(f"\n[OK] エントリーシグナル検出!")
        print(f"  方向: {result_trigger['side']}")
        print(f"  エントリー価格: {df_trigger['close'].iloc[-1]:.5f}")
        print(f"  損切り(SL): {result_trigger['sl']:.5f}")
        print(f"  利確(TP): {result_trigger['tp']:.5f}")
    else:
        print(f"\n[NG] エントリー条件を満たしていません")
    
    return result_trigger if result_trigger else result, df_trigger if result_trigger else df


def test_exit_conditions(entry_result=None, df=None):
    """エグジット条件のテスト"""
    print("\n" + "=" * 60)
    print("エグジット条件のテスト")
    print("=" * 60)
    
    strategy = BollingerStrategy(symbol="EURUSD")
    
    # エントリーシグナルを生成するためのデータ
    if df is None:
        df = generate_sample_data(num_candles=50, trigger_entry=True)
    
    # エントリー判定
    if entry_result is None:
        entry_result = strategy.should_entry(df)
    
    if not entry_result:
        print("\nエントリーシグナルがないため、エグジットテストをスキップします")
        print("（エントリーシグナルを生成するために、より多くのデータが必要かもしれません）")
        return
    
    # ポジション情報を作成
    position = {
        'side': entry_result['side'],
        'entry_price': df['close'].iloc[-1],
        'entry_time': df['time'].iloc[-1],
        'sl': entry_result['sl'],
        'tp': entry_result['tp']
    }
    
    print(f"\nポジション情報:")
    print(f"  方向: {position['side']}")
    print(f"  エントリー価格: {position['entry_price']:.5f}")
    print(f"  エントリー時刻: {position['entry_time']}")
    
    # エグジット条件を満たすデータを生成（中央線を超える動き）
    # ロングの場合：価格を中央線より上に
    # ショートの場合：価格を中央線より下に
    
    # ボリンジャーバンドを計算
    upper, middle, lower = strategy._calculate_bollinger_bands(df)
    current_middle = middle.iloc[-1]
    
    # エグジット条件を満たすように新しいデータを追加
    new_df = df.copy()
    if position['side'] == 'buy':
        # ロングの場合：価格を中央線より上に
        new_price = current_middle + 0.001
    else:
        # ショートの場合：価格を中央線より下に
        new_price = current_middle - 0.001
    
    new_candle = {
        'time': df['time'].iloc[-1] + timedelta(hours=1),
        'open': df['close'].iloc[-1],
        'high': new_price + 0.0005,
        'low': new_price - 0.0005,
        'close': new_price
    }
    
    new_df = pd.concat([new_df, pd.DataFrame([new_candle])], ignore_index=True)
    
    # エグジット判定
    should_exit = strategy.should_exit(position, new_df)
    
    if should_exit:
        print(f"\n[OK] エグジットシグナル検出!")
        print(f"  現在価格: {new_df['close'].iloc[-1]:.5f}")
        print(f"  中央線: {strategy._calculate_bollinger_bands(new_df)[1].iloc[-1]:.5f}")
    else:
        print(f"\n[NG] エグジット条件を満たしていません")
        print(f"  現在価格: {new_df['close'].iloc[-1]:.5f}")
        print(f"  中央線: {strategy._calculate_bollinger_bands(new_df)[1].iloc[-1]:.5f}")


def test_time_limit_exit(entry_result=None, df=None):
    """72時間制限のテスト"""
    print("\n" + "=" * 60)
    print("72時間制限のテスト")
    print("=" * 60)
    
    strategy = BollingerStrategy(symbol="EURUSD")
    
    # エントリーシグナルを生成
    if df is None:
        df = generate_sample_data(num_candles=50, trigger_entry=True)
    
    if entry_result is None:
        entry_result = strategy.should_entry(df)
    
    if not entry_result:
        print("\nエントリーシグナルがないため、時間制限テストをスキップします")
        return
    
    # 72時間以上前のポジションを作成
    position = {
        'side': entry_result['side'],
        'entry_price': df['close'].iloc[-1],
        'entry_time': df['time'].iloc[-1] - timedelta(hours=73),  # 73時間前
        'sl': entry_result['sl'],
        'tp': entry_result['tp']
    }
    
    print(f"\nポジション情報:")
    print(f"  方向: {position['side']}")
    print(f"  エントリー時刻: {position['entry_time']}")
    print(f"  現在時刻: {df['time'].iloc[-1]}")
    print(f"  経過時間: {(df['time'].iloc[-1] - position['entry_time']).total_seconds() / 3600:.1f}時間")
    
    # エグジット判定
    should_exit = strategy.should_exit(position, df)
    
    if should_exit:
        print(f"\n[OK] 72時間経過によりエグジットシグナル検出!")
    else:
        print(f"\n[NG] エグジット条件を満たしていません")


def main():
    """メインテスト関数"""
    print("\n" + "=" * 60)
    print("ボリンジャーバンド戦略 稼働テスト")
    print("=" * 60)
    
    try:
        # エントリー条件のテスト
        entry_result, df = test_entry_conditions()
        
        # エグジット条件のテスト（エントリー結果を使用）
        test_exit_conditions(entry_result, df)
        
        # 72時間制限のテスト（エントリー結果を使用）
        test_time_limit_exit(entry_result, df)
        
        print("\n" + "=" * 60)
        print("テスト完了")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

