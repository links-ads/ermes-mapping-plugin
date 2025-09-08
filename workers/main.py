import os
import time
import requests
from PyQt5.QtCore import QObject, pyqtSignal


class MainWorker(QObject):

    # FLAGS
    # Signals when Worker is finished, triggers clean-up and closes thread
    finished = pyqtSignal()
    # Signals when the layer is ready to be downloaded on Datalake
    layer_ready = pyqtSignal(
        str, str
    )  # Changed from str to str, str to accept both local_path and datatype_id
    # Used for INFO logging
    status_updated = pyqtSignal(str)
    log_separator = pyqtSignal()
    # Used for ERROR logging
    error = pyqtSignal(str)

    def __init__(
        self,
        api_base_url: str,
        username: str,
        password: str,
        job_id: int,
    ):
        super().__init__()
        self.api_base_url = api_base_url
        self.username = username
        self.password = password
        self.job_id = job_id
        self.access_token = None
        self.is_running = True

    def _authenticate(self):
        """
        Authenticates with the API and gets an access token.

        :returns: A dictionary containing the Authorization header with the Bearer token.
        :raises HTTPError: If the authentication request fails.
        """
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}

        auth_url = f"{self.api_base_url}/auth/login"
        data = {
            "username": self.username,
            "password": self.password,
        }

        response = requests.post(auth_url, data=data)
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]
        return {"Authorization": f"Bearer {self.access_token}"}

    def _get_job_status(self):
        """
        Gets the current status of the job.

        :returns: The job status response as a dictionary.
        :raises HTTPError: If the request fails.
        """
        headers = self._authenticate()
        status_url = f"{self.api_base_url}/jobs/{self.job_id}"

        response = requests.get(status_url, headers=headers)
        response.raise_for_status()

        return response.json()

    def _download_resource(self):
        """
        Downloads the resource for the current job using the /retrieve/{job_id} endpoint
        and saves it to a temporary cache path.

        :return: The local cache path where the downloaded resource is saved.
        :raises HTTPError: If the HTTP request to the URL fails.
        """
        retrieve_url = f"{self.api_base_url}/retrieve/{self.job_id}"
        self.status_updated.emit(
            f"Job {self.job_id} status: success - Request completed, downloading layer"
        )
        headers = self._authenticate()

        # Make the request to the retrieve endpoint
        with requests.get(retrieve_url, headers=headers, stream=True) as response:
            response.raise_for_status()
            # Try to get filename from Content-Disposition header, else fallback to job_id.zip
            content_disp = response.headers.get("Content-Disposition", "")
            filename = None
            if "filename=" in content_disp:
                filename = content_disp.split("filename=")[-1].strip('"; ')
            if not filename:
                # fallback: try to get from URL or use job_id.zip
                filename = f"{self.job_id}.zip"

            cache_dir = f"./tmp/{self.job_id}"
            os.makedirs(cache_dir, exist_ok=True)
            cache_path = os.path.join(cache_dir, filename)

            with open(cache_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        return cache_path

    def run(self):
        """
        Start polling the job status from the API.

        This method will run indefinitely until the job is completed or an exception is raised.
        When the method finishes, the `finished` signal will be emitted.

        :raises Exception: If an exception occurs while polling.
        """
        try:
            self.status_updated.emit(f"Worker: Starting to monitor job {self.job_id}")

            while self.is_running:
                try:
                    job_status = self._get_job_status()
                    status = job_status["status"]
                    result = job_status["result"]
                    status_code = job_status["status_code"]

                    if status == "end":
                        # Job completed successfully
                        if job_status.get("resource_url"):
                            local_path = self._download_resource()
                            # Emit also the datatype_id associated to the job
                            datatype_id = job_status.get("body", {}).get("datatype_id")
                            self.layer_ready.emit(local_path, datatype_id)
                        else:
                            self.error.emit(
                                "Job completed but no resource URL provided"
                            )
                        break
                    elif status == "error":
                        # Job failed
                        if (
                            status_code == 404
                        ):  # Minor hack for error given on missing images (will fix in pipeline)
                            self.status_updated.emit(f"Job Warning: {result}")
                            time.sleep(5)
                        else:
                            self.error.emit(f"Job Error: {status_code} - {result}")
                            self.log_separator.emit()
                            break
                    elif status in ["pending", "start", "update"]:
                        # Job is still running, wait before checking again
                        self.status_updated.emit(
                            f"Job {self.job_id} status: {status} - {result} "
                        )
                        time.sleep(1)  # Poll every 5 seconds
                    else:
                        self.error.emit(f"Unknown job status: {status}")
                        self.log_separator.emit()
                        break

                except requests.exceptions.RequestException as e:
                    self.error.emit(f"API request error: {e}")
                    self.log_separator.emit()
                    break

        except Exception as e:
            self.error.emit(f"Worker Error: {e}")
        finally:
            self.finished.emit()

    def stop(self):
        """Stops the worker. Called when the plugin is closed."""
        self.status_updated.emit("Worker: Stopping...")
        self.is_running = False
