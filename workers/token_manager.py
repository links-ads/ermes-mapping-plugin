import requests
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, pyqtSignal


class TokenManager(QObject):
    """
    Manages token validation and expiration checking.
    Provides signals for token expiration events.
    Uses token age tracking instead of JWT parsing.
    """

    # Signals
    token_expired = pyqtSignal()  # Emitted when token is expired
    token_refresh_needed = pyqtSignal()  # Emitted when token needs refresh

    def __init__(self, api_base_url: str, config):
        super().__init__()
        self.api_base_url = api_base_url
        self.config = config
        self.access_token = None
        self.token_created_at = None
        
        # Get token lifetime from config
        self.token_lifetime_minutes = self.config.token_lifetime_minutes
        self.expiration_buffer_minutes = self.config.token_expiration_buffer_minutes
        self.api_validation_timeout = self.config.token_api_validation_timeout

    def set_token(self, access_token: str, lifetime_minutes: int = None):
        """Set the access token and track its creation time"""
        self.access_token = access_token
        self.token_created_at = datetime.now()
        if lifetime_minutes is not None:
            self.token_lifetime_minutes = lifetime_minutes

    def is_token_expired(self) -> bool:
        """Check if the current token is expired based on age"""
        if not self.access_token or not self.token_created_at:
            return True

        # Calculate token age
        token_age = datetime.now() - self.token_created_at
        token_lifetime = timedelta(minutes=self.token_lifetime_minutes)

        # Add a buffer to avoid edge cases
        buffer_time = timedelta(minutes=self.expiration_buffer_minutes)
        return token_age >= (token_lifetime - buffer_time)

    def is_token_valid(self) -> bool:
        """Check if the token is valid (not expired)"""
        return not self.is_token_expired()

    def get_time_until_expiry(self) -> timedelta:
        """Get the time remaining until token expires"""
        if not self.token_created_at:
            return timedelta(0)

        token_age = datetime.now() - self.token_created_at
        token_lifetime = timedelta(minutes=self.token_lifetime_minutes)
        remaining_time = token_lifetime - token_age

        return max(remaining_time, timedelta(0))

    def validate_token_with_api(self) -> bool:
        """
        Validate the token by making a test API call.
        Returns True if token is valid, False otherwise.
        """
        if not self.access_token:
            return False

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            # Use a lightweight endpoint to test token validity
            test_url = f"{self.api_base_url}{self.config.api_endpoints['jobs_list']}"
            response = requests.get(test_url, headers=headers, timeout=self.api_validation_timeout)

            if response.status_code == 401:
                # Token is invalid/expired
                return False
            elif response.status_code == 200:
                # Token is valid
                return True
            else:
                # Other error, assume token is still valid
                return True

        except requests.exceptions.RequestException:
            # Network error, assume token is still valid to avoid false positives
            return True
        except Exception:
            # Other error, assume token is still valid
            return True

    def check_and_handle_expiration(self) -> bool:
        """
        Check if token is expired and emit appropriate signals.
        Returns True if token is still valid, False if expired.
        """
        if self.is_token_expired():
            self.token_expired.emit()
            return False

        # Also validate with API to catch server-side token expiration
        if not self.validate_token_with_api():
            self.token_expired.emit()
            return False

        return True

    def clear_token(self):
        """Clear the stored token and creation time"""
        self.access_token = None
        self.token_created_at = None
