import time
import requests
from PyQt5.QtCore import QObject, pyqtSignal
from .token_manager import TokenManager


class JobsWorker(QObject):
    """Worker for fetching jobs from the API"""

    # Signals
    jobs_updated = pyqtSignal(list)  # Emits list of jobs
    error = pyqtSignal(str)  # Emits error messages
    finished = pyqtSignal()  # Emits when worker is finished

    def __init__(self, api_base_url: str, access_token: str, config):
        super().__init__()
        self.api_base_url = api_base_url
        self.access_token = access_token
        self.config = config
        self.is_running = True
        self.token_manager = TokenManager(api_base_url, config)
        self.token_manager.set_token(access_token)

    def _authenticate(self):
        """Returns authentication headers after checking token validity"""
        # Check if token is still valid
        if not self.token_manager.check_and_handle_expiration():
            # Token is expired, emit error signal
            self.error.emit("Authentication token has expired. Please login again.")
            return None
        return {"Authorization": f"Bearer {self.access_token}"}

    def _get_jobs(self):
        """Fetches all jobs for the current user"""
        headers = self._authenticate()
        if headers is None:
            return []  # Token expired, return empty list

        jobs_url = f"{self.api_base_url}{self.config.api_endpoints['jobs_list']}"

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
