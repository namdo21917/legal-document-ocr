import logging
import os
from datetime import datetime

class Logger:
    def __init__(self, config):
        self.logger = logging.getLogger('OCRService')
        self.logger.setLevel(config['logging']['level'])

        # File handler
        log_file = f"logs/ocr_{datetime.now().strftime('%Y%m%d')}.log"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        fh = logging.FileHandler(log_file)
        fh.setFormatter(logging.Formatter(config['logging']['format']))
        self.logger.addHandler(fh)

        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter(config['logging']['format']))
        self.logger.addHandler(ch) 