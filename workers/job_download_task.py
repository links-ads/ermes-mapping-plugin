import os
import requests
import tempfile
from qgis.core import QgsTask
from PyQt5.QtCore import pyqtSignal
from .token_manager import TokenManager


class JobDownloadTask(QgsTask):
    """QgsTask for downloading job resources from the API asynchronously"""

    # Signals for safe communication with main thread
    status_update = pyqtSignal(str, str)  # message, level
    download_completed = pyqtSignal(str, str)  # file_path, datatype_id
    download_failed = pyqtSignal(str)  # error message

    def __init__(
        self,
        description,
        job_id,
        api_base_url,
        access_token,
        dialog_ref,
        config,
    ):
        super().__init__(description, QgsTask.CanCancel)
        self.job_id = job_id
        self.api_base_url = api_base_url
        self.access_token = access_token
        self.dialog_ref = dialog_ref
        self.config = config
        self.result_path = None
        self.datatype_id = None
        self.error_message = None
        self.total_size = 0
        self.downloaded_size = 0

        # Initialize token manager
        self.token_manager = TokenManager(api_base_url, config)
        self.token_manager.set_token(access_token)

    def _authenticate(self):
        """Returns authentication headers after checking token validity"""
        # Check if token is still valid
        if not self.token_manager.check_and_handle_expiration():
            self.error_message = "Authentication token has expired. Please login again."
            return None
        return {"Authorization": f"Bearer {self.access_token}"}

    def run(self):
        """
        Run the job download task. This runs in a background thread.
        Returns True if successful, False if failed.
        """
        try:
            # Set progress and update status
            self.setProgress(1)
            self.status_update.emit(f"Preparing to download job {self.job_id}...", "info")

            # Check if task was cancelled
            if self.isCanceled():
                return False

            # Get authentication headers
            self.setProgress(5)
            headers = self._authenticate()
            if headers is None:
                return False  # Error already set

            # First, get the job details to retrieve the datatype_id
            self.setProgress(10)
            self.status_update.emit(f"Fetching job details for {self.job_id}...", "info")
            
            job_url = f"{self.api_base_url}{self.config.api_endpoints['jobs_detail'].format(job_id=self.job_id)}"
            
            job_response = requests.get(job_url, headers=headers)
            job_response.raise_for_status()
            job_data = job_response.json()

            # Extract datatype_id from the job data
            self.datatype_id = job_data.get("body", {}).get("datatype_id", None)

            # Check if task was cancelled
            if self.isCanceled():
                return False

            # Get the retrieve URL
            self.setProgress(15)
            retrieve_url = f"{self.api_base_url}{self.config.api_endpoints['retrieve'].format(job_id=self.job_id)}"
            self.status_update.emit(f"Starting download for job {self.job_id}...", "info")

            # Download the file
            with requests.get(retrieve_url, headers=headers, stream=True) as response:
                response.raise_for_status()

                # Get content length for progress tracking
                self.total_size = int(response.headers.get('Content-Length', 0))
                
                # Get filename from Content-Disposition header
                content_disp = response.headers.get("Content-Disposition", "")
                filename = None
                if "filename=" in content_disp:
                    filename = content_disp.split("filename=")[-1].strip('"; ')
                if not filename:
                    filename = f"{self.job_id}.zip"

                # Use a temporary directory to save the file
                temp_dir = tempfile.mkdtemp(prefix=f"{self.config.temp_dir_prefix}{self.job_id}_")
                cache_path = os.path.join(temp_dir, filename)
                self.result_path = cache_path  # Store for cleanup later

                # Download with progress tracking
                self.downloaded_size = 0
                chunk_size = self.config.processing_chunk_size
                
                with open(cache_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        # Check if task was cancelled
                        if self.isCanceled():
                            os.remove(cache_path)
                            os.rmdir(temp_dir)
                            return False
                        
                        if chunk:
                            f.write(chunk)
                            self.downloaded_size += len(chunk)
                            
                            # Update progress based on downloaded bytes
                            if self.total_size > 0:
                                progress = int((self.downloaded_size / self.total_size) * 100)
                                progress = max(20, min(95, progress))  # Keep progress between 20-95%
                                self.setProgress(progress)


            self.setProgress(100)
            self.status_update.emit(f"Download completed for job {self.job_id}!", "success")

            # Manually emit the completion signal
            self.download_completed.emit(self.result_path, self.datatype_id)
            return True

        except requests.exceptions.RequestException as e:
            self.error_message = f"Network error during download: {e}"
            self.status_update.emit(f"Network error: {e}", "error")
            self.download_failed.emit(self.error_message)
            return False
        except Exception as e:
            self.error_message = f"Error during download: {e}"
            self.status_update.emit(f"Download error: {e}", "error")
            self.download_failed.emit(self.error_message)
            return False

    def finished(self, result):
        """
        Called when the task is finished. This runs in the main thread.
        """
        if result and self.result_path:
            # Success - emit signal to load the layer
            self.download_completed.emit(self.result_path, self.datatype_id)
        else:
            # Failure - emit error signal
            error_msg = self.error_message or "Download failed"
            self.download_failed.emit(error_msg)

    def cancel(self):
        """Called when the task is cancelled"""
        super().cancel()
        self.download_failed.emit("Download cancelled")
