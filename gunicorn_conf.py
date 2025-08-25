# Gunicorn production configuration
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
graceful_timeout = 30
preload_app = True

# Logging
accesslog = '-'  # stdout
errorlog = '-'   # stdout
loglevel = 'info'
