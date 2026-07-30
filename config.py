from pathlib import Path
from dotenv import load_dotenv
import os

# Proje kök klasörü
ROOT = Path(__file__).parent

# .env dosyasını yükle
load_dotenv(ROOT / ".env")

# Ortam değişkenlerini Python değişkenlerine aktar
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Kontrol
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY .env dosyasında bulunamadı.")