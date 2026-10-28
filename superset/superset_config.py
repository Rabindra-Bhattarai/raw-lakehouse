import os

# Local demo only. A real deployment needs a long random secret from a secret store.
SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "local-demo-secret-change-me")
SQLALCHEMY_DATABASE_URI = "sqlite:////app/superset_home/superset.db"

# Small laptop: keep caching simple and in memory.
CACHE_CONFIG = {"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 30}
DATA_CACHE_CONFIG = CACHE_CONFIG
