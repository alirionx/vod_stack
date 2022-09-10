from settings import app_settings
from tools import JobWorker


if __name__ == "__main__":
  job_worker = JobWorker()
  job_worker.start_consuming_jobs()