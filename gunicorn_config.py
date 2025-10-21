# Gunicorn configuration for Render Free Tier
# Optimized for 512MB RAM constraint

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:" + os.getenv("PORT", "10000")
backlog = 2048

# Worker processes - REDUCED for free tier
# Free tier: 1 worker to stay within 512MB memory limit
# Paid tier: uncomment the line below for better performance
workers = 1  # Free tier
# workers = min(multiprocessing.cpu_count() * 2 + 1, 4)  # Paid tier

# Worker class
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120  # Increased for file processing operations
keepalive = 5

# Process naming
proc_name = "cropio"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
def on_starting(server):
    print("🚀 Starting Cropio on Render Free Tier")
    print(f"📊 Workers: {workers}")
    print(f"🔌 Binding to: {bind}")

def on_reload(server):
    print("🔄 Reloading Cropio...")

def worker_int(worker):
    print(f"⚠️ Worker received INT or QUIT signal: {worker.pid}")

def worker_abort(worker):
    print(f"❌ Worker received SIGABRT signal: {worker.pid}")

