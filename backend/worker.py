import os
from arq import cron
from arq.connections import RedisSettings

# Import the task
from services.alerts.escalation_engine import run_escalation_checks

# Parse Redis URL from environment or use default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# arq requires RedisSettings (which can be instantiated from a DSN)
redis_settings = RedisSettings.from_dsn(REDIS_URL)

class WorkerSettings:
    """
    Settings for the arq worker process.
    Run via: arq worker.WorkerSettings
    """
    redis_settings = redis_settings
    
    # Cron jobs
    cron_jobs = [
        # Run the escalation check every minute
        cron(run_escalation_checks, minute=None), 
    ]
    
    # Standard functions that can be queued dynamically
    functions = [
        run_escalation_checks
    ]
