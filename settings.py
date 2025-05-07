import os
from core.utils import str_to_bool

if os.environ.get("ENVIRONTMENT") != "prod":
    from dotenv import load_dotenv

    load_dotenv()

# Environtment
ENVIRONTMENT = os.environ.get("ENVIRONTMENT", "development")

# CORS
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")

# APACHE KAFKA
KAFKA_SERVER = os.environ.get("KAFKA_SERVER")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC")
RESPONSES_TOPIC = os.environ.get("RESPONSES_TOPIC")

# Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_KEY_SERVICE = os.environ.get("SUPABASE_KEY_SERVICE")

# JWT conf
JWT_PREFIX = os.environ.get("JWT_PREFIX", "Bearer")
SECRET_KEY = os.environ.get("SECRET_KEY", "98yt7ftdviuqedfhcu4gr894c2nr")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Timezone
TZ = os.environ.get("TZ", "Asia/Jakarta")

# Email
MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
MAIL_FROM = os.environ.get("MAIL_FROM", "test@yopmail.com")
MAIL_PORT = int(os.environ.get("MAIL_PORT", "465"))
MAIL_SERVER = os.environ.get("MAIL_SERVER", "")
MAIL_FROM_NAME = os.environ.get("MAIL_FROM_NAME", "test@yopmail.com")
MAIL_TLS = str_to_bool(os.environ.get("MAIL_TLS", "False"))
MAIL_SSL = str_to_bool(os.environ.get("MAIL_SSL", "True"))
USE_CREDENTIALS = str_to_bool(os.environ.get("USE_CREDENTIALS", "True"))

# Frontend Domain
FE_DOMAIN = os.environ.get("FE_DOMAIN", "")

# backend url
BACKEND_URL = os.environ.get("BACKEND_URL", "")

# local path
LOCAL_PATH = os.environ.get("LOCAL_PATH", "./storage")

# Minio
MINIO_ENPOINT = os.environ.get("MINIO_ENPOINT", "")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "")
MINIO_SECURE = str_to_bool(os.environ.get("MINIO_SECURE", "False"))
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "ticketing")

# Sentry
SENTRY_DSN = os.environ.get("SENTRY_DSN", None)
SENTRY_TRACES_SAMPLE_RATES = float(os.environ.get("SENTRY_TRACES_SAMPLE_RATES", 1.0))

# Redis
REDIS_HOST = os.environ.get("REDIS_HOST", None)
REDIS_PORT = int(os.environ.get("REDIS_PORT", "0"))
REDIS_DB = int(os.environ.get("REDIS_DB", "0"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# File Storage adapter
FILE_STORAGE_ADAPTER = os.environ.get("FILE_STORAGE_ADAPTER", "minio")
if not FILE_STORAGE_ADAPTER in ["local", "minio"]:
    raise Exception(
        "Invalid FILE_STORAGE_ADAPTER, FILE_STORAGE_ADAPTER should local or minio"
    )

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "uhuhuhuhu")
DEFAULT_SCHEMA = os.environ.get("DEFAULT_SCHEMA", None)
DEFAULT_ROLE_PASSWORD = os.environ.get("DEFAULT_ROLE_PASSWORD", None)
DEFAULT_DB_USERNAME = os.environ.get("DEFAULT_DB_USERNAME", None)   

SUPER_ROLE_DB = os.environ.get("SUPER_ROLE_DB", None)
SUPPER_ROLE_PASSWORD = os.environ.get("SUPPER_ROLE_PASSWORD", None)
SUPER_DB_HOST = os.environ.get("SUPER_DB_HOST", None)
SUPER_DB_NAME = os.environ.get("SUPER_DB_NAME", None)
