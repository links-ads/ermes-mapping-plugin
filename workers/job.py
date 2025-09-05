import time
import requests
from PyQt5.QtCore import QObject, pyqtSignal


class JobsWorker(QObject):
    """Worker for fetching jobs from the API"""

    # Signals
    jobs_updated = pyqtSignal(list)  # Emits list of jobs
    error = pyqtSignal(str)  # Emits error messages
    finished = pyqtSignal()  # Emits when worker is finished

    def __init__(self, api_base_url: str, access_token: str):
        super().__init__()
        self.api_base_url = api_base_url
        self.access_token = access_token
        self.is_running = True

    def _authenticate(self):
        """Returns authentication headers"""
        return {"Authorization": f"Bearer {self.access_token}"}

    def _get_jobs(self):
        """Fetches all jobs for the current user"""
        headers = self._authenticate()
        jobs_url = f"{self.api_base_url}/jobs/"

        response = requests.get(jobs_url, headers=headers)
        response.raise_for_status()

        return response.json()["jobs"]

    def run(self):
        """Main worker loop - fetches jobs every 30 seconds"""
        try:
            while self.is_running:
                try:
                    jobs = self._get_jobs()
                    self.jobs_updated.emit(jobs)
                except requests.exceptions.RequestException as e:
                    self.error.emit(f"Failed to fetch jobs: {e}")
                except Exception as e:
                    self.error.emit(f"Unexpected error: {e}")

                # Wait 30 seconds before next fetch
                for _ in range(30):
                    if not self.is_running:
                        break
                    time.sleep(1)

        except Exception as e:
            self.error.emit(f"Worker error: {e}")
        finally:
            self.finished.emit()

    def stop(self):
        """Stops the worker"""
        self.is_running = False
