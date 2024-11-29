import hashlib
import pickle
import time
from datetime import datetime, timedelta

class CacheManager:
    def __init__(self, max_size=1000, ttl_hours=24):
        self.cache = {}
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)

    def generate_key(self, data):
        """Tạo key cho cache từ dữ liệu"""
        return hashlib.md5(pickle.dumps(data)).hexdigest()

    def get(self, key):
        """Lấy dữ liệu từ cache"""
        if key in self.cache:
            item = self.cache[key]
            if datetime.now() - item['timestamp'] < self.ttl:
                return item['data']
            else:
                del self.cache[key]
        return None

    def set(self, key, value):
        """Lưu dữ liệu vào cache"""
        if len(self.cache) >= self.max_size:
            self._cleanup()
            
        self.cache[key] = {
            'data': value,
            'timestamp': datetime.now()
        }

    def _cleanup(self):
        """Dọn dẹp cache cũ"""
        current_time = datetime.now()
        self.cache = {
            k: v for k, v in self.cache.items()
            if current_time - v['timestamp'] < self.ttl
        } 