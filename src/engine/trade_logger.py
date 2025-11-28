"""
トレードログ自動保存機能
"""
import os
import csv
from datetime import datetime
import threading

try:
    import portalocker
    HAS_PORTALOCKER = True
except ImportError:
    HAS_PORTALOCKER = False
    # Windows用の代替実装
    try:
        import msvcrt
        HAS_MSVCRT = True
    except ImportError:
        HAS_MSVCRT = False


class TradeLogger:
    """トレードログをCSVファイルに保存するクラス"""
    
    def __init__(self, log_file="logs/trades.csv"):
        """
        トレードロガーを初期化
        
        Args:
            log_file: ログファイルのパス
        """
        self.log_file = log_file
        self.lock = threading.Lock()
        
        # ログディレクトリが存在しない場合は作成
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # CSVファイルが存在しない場合はヘッダーを作成
        if not os.path.exists(log_file):
            self._write_header()
    
    def _write_header(self):
        """CSVファイルのヘッダーを書き込む"""
        headers = [
            "timestamp",
            "strategy",
            "symbol",
            "direction",
            "entry_price",
            "stop_loss",
            "take_profit",
            "volume",
            "ticket",
            "result",
            "profit",
            "balance_after"
        ]
        
        with self._lock_file(mode='w') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
    
    def _lock_file(self, mode='a'):
        """
        ファイルロックを取得するコンテキストマネージャー
        
        Args:
            mode: ファイルモード（'a'=追記, 'w'=書き込み）
        """
        if HAS_PORTALOCKER:
            # portalockerを使用（クロスプラットフォーム）
            return portalocker.Lock(self.log_file, mode=mode, flags=portalocker.LOCK_EX)
        elif HAS_MSVCRT:
            # Windows用のmsvcrtを使用
            class WindowsFileLock:
                def __init__(self, filepath, mode):
                    self.filepath = filepath
                    self.mode = mode
                    self.file = None
                
                def __enter__(self):
                    self.file = open(self.filepath, self.mode, encoding='utf-8', newline='')
                    # ファイル全体をロック（1バイト目からファイル終端まで）
                    try:
                        msvcrt.locking(self.file.fileno(), msvcrt.LK_LOCK, 1)
                    except (OSError, IOError):
                        # ロックに失敗した場合はスキップ（フォールバック）
                        pass
                    return self.file
                
                def __exit__(self, exc_type, exc_val, exc_tb):
                    if self.file:
                        try:
                            msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, 1)
                        except (OSError, IOError):
                            pass
                        self.file.close()
            
            return WindowsFileLock(self.log_file, mode)
        else:
            # フォールバック: スレッドロックのみ（ファイルロックなし）
            class ThreadLockOnly:
                def __init__(self, filepath, lock, mode):
                    self.filepath = filepath
                    self.lock = lock
                    self.mode = mode
                    self.file = None
                
                def __enter__(self):
                    self.lock.acquire()
                    self.file = open(self.filepath, self.mode, encoding='utf-8', newline='')
                    return self.file
                
                def __exit__(self, exc_type, exc_val, exc_tb):
                    if self.file:
                        self.file.close()
                    self.lock.release()
            
            return ThreadLockOnly(self.log_file, self.lock, mode)
    
    def log_trade(self, entry_dict):
        """
        エントリー時のトレードログを記録
        
        Args:
            entry_dict: エントリー情報の辞書
                - timestamp: エントリー時刻（datetimeまたは文字列）
                - strategy: 戦略名
                - symbol: 通貨ペア
                - direction: "buy" または "sell"
                - entry_price: エントリー価格
                - stop_loss: 損切り価格
                - take_profit: 利確価格（None可）
                - volume: ロット数
                - ticket: MT5の注文番号
        """
        # タイムスタンプを文字列に変換
        if isinstance(entry_dict.get('timestamp'), datetime):
            timestamp = entry_dict['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        else:
            timestamp = entry_dict.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        row = [
            timestamp,
            entry_dict.get('strategy', ''),
            entry_dict.get('symbol', ''),
            entry_dict.get('direction', ''),
            entry_dict.get('entry_price', ''),
            entry_dict.get('stop_loss', ''),
            entry_dict.get('take_profit', '') if entry_dict.get('take_profit') is not None else '',
            entry_dict.get('volume', ''),
            entry_dict.get('ticket', ''),
            'entry',
            '',  # profit（エントリー時は空欄）
            ''   # balance_after（エントリー時は空欄）
        ]
        
        with self._lock_file(mode='a') as f:
            writer = csv.writer(f)
            writer.writerow(row)
    
    def log_close(self, close_dict):
        """
        決済時のトレードログを記録
        
        Args:
            close_dict: 決済情報の辞書
                - timestamp: 決済時刻（datetimeまたは文字列）
                - strategy: 戦略名
                - symbol: 通貨ペア
                - direction: "buy" または "sell"
                - entry_price: エントリー価格
                - stop_loss: 損切り価格
                - take_profit: 利確価格（None可）
                - volume: ロット数
                - ticket: MT5の注文番号
                - profit: 利益
                - balance_after: 決済後の残高
        """
        # タイムスタンプを文字列に変換
        if isinstance(close_dict.get('timestamp'), datetime):
            timestamp = close_dict['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        else:
            timestamp = close_dict.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        row = [
            close_dict.get('entry_timestamp', timestamp),  # エントリー時刻を使用
            close_dict.get('strategy', ''),
            close_dict.get('symbol', ''),
            close_dict.get('direction', ''),
            close_dict.get('entry_price', ''),
            close_dict.get('stop_loss', ''),
            close_dict.get('take_profit', '') if close_dict.get('take_profit') is not None else '',
            close_dict.get('volume', ''),
            close_dict.get('ticket', ''),
            'exit',
            close_dict.get('profit', ''),
            close_dict.get('balance_after', '')
        ]
        
        with self._lock_file(mode='a') as f:
            writer = csv.writer(f)
            writer.writerow(row)

