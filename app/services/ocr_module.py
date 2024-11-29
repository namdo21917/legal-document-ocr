import tesserocr
from PIL import Image
import multiprocessing
from app.utils.cache_manager import CacheManager

class OCRModule:
    def __init__(self):
        self.cache = CacheManager()
        self.num_threads = multiprocessing.cpu_count()

    def process_image(self, image):
        """Xử lý OCR cho một ảnh"""
        # Kiểm tra cache
        cache_key = self.cache.generate_key(image)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result

        # Thực hiện OCR
        with tesserocr.PyTessBaseAPI() as api:
            api.SetImage(Image.fromarray(image))
            text = api.GetUTF8Text()
            confidence = api.MeanTextConf()

        result = {
            'text': text,
            'confidence': confidence
        }

        # Lưu vào cache
        self.cache.set(cache_key, result)
        
        return result

    def process_batch(self, images):
        """Xử lý OCR đa luồng cho nhiều ảnh"""
        with multiprocessing.Pool(self.num_threads) as pool:
            results = pool.map(self.process_image, images)
        return results 