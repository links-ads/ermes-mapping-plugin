import os
import requests
import tempfile
from qgis.core import QgsTask
from PyQt5.QtCore import pyqtSignal
from .token_manager import TokenManager


class FileUploadTask(QgsTask):
    """QgsTask for uploading files to the API asynchronously"""

    # Signals for safe communication with main thread
    status_update = pyqtSignal(str, str)  # message, level
    upload_completed = pyqtSignal(str, str)  # file_path, datatype_id
    upload_failed = pyqtSignal(str)  # error message

    def __init__(
        self,
        description,
        file_path,
        datatype_id,
        image_type,
        api_base_url,
        access_token,
        dialog_ref,
        config,
    ):
        super().__init__(description, QgsTask.CanCancel)
        self.file_path = file_path
        self.datatype_id = datatype_id
        self.image_type = image_type
        self.api_base_url = api_base_url
        self.access_token = access_token
        self.dialog_ref = dialog_ref
        self.config = config
        self.result_path = None
        self.error_message = None

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
        Run the file upload task. This runs in a background thread.
        Returns True if successful, False if failed.
        """
        try:
            filename = os.path.basename(self.file_path)

            # Set progress and update status
            self.setProgress(5)
            self.status_update.emit(f"Preparing to upload {filename}...", "info")

            # Check if task was cancelled
            if self.isCanceled():
                return False

            # Get authentication headers
            self.setProgress(10)
            headers = self._authenticate()
            if headers is None:
                return False  # Error already set

            # Prepare the API endpoint and parameters
            job_url = f"{self.api_base_url}{self.config.api_endpoints['jobs_create_from_file']}"
            params = {
                "datatype_id": self.datatype_id,
                "image_type": self.image_type,
            }

            self.setProgress(15)
            self.status_update.emit(f"Uploading {filename} to server...", "info")

            # Check if task was cancelled
            if self.isCanceled():
                return False

            # Get file size for progress tracking and validation
            file_size = os.path.getsize(self.file_path)
            file_size_mb = file_size / (1024 * 1024)
            self.status_update.emit(f"File size: {file_size_mb:.1f} MB", "info")

            # Check file size limit (1 GB = 1024 MB)
            if file_size > 1024 * 1024 * 1024:  # 1 GB in bytes
                self.error_message = f"File too large: {file_size_mb:.1f} MB. Maximum allowed size is 1 GB (1024 MB)."
                self.status_update.emit(self.error_message, "error")
                self.upload_failed.emit(self.error_message)
                return False

            # Open the raster file for upload
            with open(self.file_path, "rb") as f:
                files = {
                    "file": (filename, f, "image/tiff"),
                }

                self.setProgress(20)

                # Make the request with timeout and progress tracking
                try:
                    self.status_update.emit(
                        "Upload and inference in progress (this may take several minutes)...",
                        "info",
                    )

                    response = requests.post(
                        job_url,
                        headers=headers,
                        params=params,
                        files=files,
                        timeout=6000,
                    )
                    response.raise_for_status()

                except requests.exceptions.Timeout:
                    self.error_message = (
                        "Upload timeout - the file may be too large or server is slow"
                    )
                    self.status_update.emit(
                        "Upload timeout - please try again", "error"
                    )
                    return False

            self.setProgress(70)
            self.status_update.emit(
                "Inference completed, processing response...", "info"
            )

            # Check if task was cancelled
            if self.isCanceled():
                return False

            # Check the response content type
            content_type = response.headers.get("Content-Type", "")
            if "image/tiff" in content_type or "image/tif" in content_type:
                self.setProgress(85)
                self.status_update.emit("Saving result TIFF file...", "info")

                # Save the response to a temporary file
                temp_tiff = tempfile.NamedTemporaryFile(delete=False, suffix=".tif")
                temp_tiff.write(response.content)
                temp_tiff.close()

                self.result_path = temp_tiff.name
                self.setProgress(100)
                self.status_update.emit("Inference completed successfully!", "success")

                # Manually emit the completion signal since finished() might not be called
                self.upload_completed.emit(self.result_path, self.datatype_id)
                return True
            else:
                # If the API returns JSON (e.g., error), extract the message
                try:
                    error_json = response.json()
                    error_msg = error_json.get("detail", str(error_json))
                except Exception:
                    error_msg = response.text
                self.error_message = f"API returned error: {error_msg}"
                self.status_update.emit(f"Error: {error_msg}", "error")
                self.upload_failed.emit(self.error_message)
                return False

        except requests.exceptions.RequestException as e:
            self.error_message = f"Network error during inference: {e}"
            self.status_update.emit(f"Network error: {e}", "error")
            self.upload_failed.emit(self.error_message)
            return False
        except Exception as e:
            self.error_message = f"Error during inference: {e}"
            self.status_update.emit(f"Upload error: {e}", "error")
            self.upload_failed.emit(self.error_message)
            return False

    def finished(self, result):
        """
        Called when the task is finished. This runs in the main thread.
        """

        if result and self.result_path:
            # Success - emit signal to load the layer
            self.upload_completed.emit(self.result_path, self.datatype_id)
        else:
            # Failure - emit error signal
            error_msg = self.error_message or "Inference failed"
            self.upload_failed.emit(error_msg)

    def cancel(self):
        """Called when the task is cancelled"""
        super().cancel()
        self.upload_failed.emit("Inference cancelled")
