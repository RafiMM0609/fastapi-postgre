# logging_config.py
import logging

# Konfigurasi dasar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Buat instance logger
logger = logging.getLogger(__name__)
