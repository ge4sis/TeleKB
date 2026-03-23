import sqlite3
import time
from typing import List, Optional, Tuple

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.init_db()

    def get_connection(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Channels table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                channel_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                username TEXT,
                last_message_id INTEGER DEFAULT 0,
                is_enabled INTEGER DEFAULT 1,
                created_at INTEGER,
                updated_at INTEGER
            )
        ''')
        
        # Messages table (to prevent duplicates)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                message_id INTEGER,
                file_path TEXT,
                created_at INTEGER,
                UNIQUE(channel_id, message_id)
            )
        ''')
        
        conn.commit()

    def add_channel(self, channel_id: int, title: str, username: Optional[str], last_message_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        now = int(time.time())
        try:
            cursor.execute('''
                INSERT INTO channels (channel_id, title, username, last_message_id, is_enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            ''', (channel_id, title, username, last_message_id, now, now))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Already exists, just enable it if disabled? Spec says:
            # "추가한 시점 이후의 메시지부터 수집 대상이 된다." -> re-adding logic might be needed if it was fully deleted?
            # But here we are just adding. If it exists, maybe we should update last_message_id if it was disabled?
            # Spec 3.3 says "Soft delete".
            # If re-adding a soft-deleted channel, we should re-enable it and update last_message_id?
            # Spec 3.3: "제거 후 재추가 시에도 “추가 시점 이후만 수집” 정책으로 과거 재생성은 발생하지 않아야 한다."  
             cursor.execute('''
                UPDATE channels 
                SET is_enabled = 1, last_message_id = ?, updated_at = ?
                WHERE channel_id = ?
            ''', (last_message_id, now, channel_id))
             conn.commit()
             return True
        except Exception as e:
            print(f"Error adding channel: {e}")
            return False

    def get_channels(self, only_enabled=True) -> List[sqlite3.Row]:
        conn = self.get_connection()
        cursor = conn.cursor()
        if only_enabled:
            cursor.execute("SELECT * FROM channels WHERE is_enabled = 1")
        else:
            cursor.execute("SELECT * FROM channels")
        return cursor.fetchall()
        
    def delete_channel(self, channel_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
        conn.commit()

    def update_last_message_id(self, channel_id: int, message_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        # Only update if new message_id is greater than current? 
        # Ideally yes, but the caller should handle logic. We just update.
        # But wait, we might process messages in parallel or out of order? 
        # Spec 3.4 says "성공적으로 저장된 메시지 중 최대 message_id로 해당 채널의 last_message_id를 갱신한다."
        # So we should probably check MAX.
        cursor.execute("UPDATE channels SET last_message_id = MAX(last_message_id, ?) WHERE channel_id = ?", (message_id, channel_id))
        conn.commit()

    def is_message_processed(self, channel_id: int, message_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM messages WHERE channel_id = ? AND message_id = ?", (channel_id, message_id))
        return cursor.fetchone() is not None

    def save_message_log(self, channel_id: int, message_id: int, file_path: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        now = int(time.time())
        try:
            cursor.execute("INSERT INTO messages (channel_id, message_id, file_path, created_at) VALUES (?, ?, ?, ?)", (channel_id, message_id, file_path, now))
            conn.commit()
        except sqlite3.IntegrityError:
            pass # Already processed

    def update_channel_title(self, channel_id: int, title: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        now = int(time.time())
        cursor.execute("UPDATE channels SET title = ?, updated_at = ? WHERE channel_id = ?", (title, now, channel_id))
        conn.commit()

    def get_sync_data(self) -> List[dict]:
        """Returns all channel metadata for synchronization."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id, title, username, last_message_id, is_enabled FROM channels")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def update_from_sync_data(self, sync_data: List[dict]):
        """Updates local database from synchronization data."""
        conn = self.get_connection()
        cursor = conn.cursor()
        now = int(time.time())
        for item in sync_data:
            channel_id = item['channel_id']
            title = item['title']
            username = item.get('username')
            last_message_id = item['last_message_id']
            is_enabled = item.get('is_enabled', 1)
            
            cursor.execute("SELECT 1 FROM channels WHERE channel_id = ?", (channel_id,))
            if cursor.fetchone():
                # Update existing channel
                cursor.execute('''
                    UPDATE channels 
                    SET title = ?, username = ?, last_message_id = MAX(last_message_id, ?), is_enabled = ?, updated_at = ?
                    WHERE channel_id = ?
                ''', (title, username, last_message_id, is_enabled, now, channel_id))
            else:
                # Add new channel from sync
                cursor.execute('''
                    INSERT INTO channels (channel_id, title, username, last_message_id, is_enabled, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (channel_id, title, username, last_message_id, is_enabled, now, now))
        conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
