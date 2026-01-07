import pandas as pd
import threading
import os

class ProductDataManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ProductDataManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.df = None
        self._initialized = True
        
    def load_data(self, file_path: str):
        """Loads CSV data into memory once."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Optimize: Load only necessary columns if known, but for now load all
        self.df = pd.read_csv(file_path)
        print(f"Loaded {len(self.df)} products from {file_path}")
        
    def get_df(self):
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        return self.df

product_data_manager = ProductDataManager()
