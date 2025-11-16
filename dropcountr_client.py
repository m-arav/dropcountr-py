import httpx
import json
from uritemplate import URITemplate
from typing import Any, Dict, Optional
from datetime import datetime, timedelta


class DropcountrClient:
    LOGIN_URL = "https://dropcountr.com/login"
    USER_DISCOVERY_API = "https://dropcountr.com/api/me"
    LOGOUT_URL = "https://dropcountr.com/api/logout"

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self._http_client: Optional[httpx.Client] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the HTTP client session."""
        if self._http_client:
            self._http_client.close()
            self._http_client = None

    @property
    def http(self) -> httpx.Client:
        """Lazy-load HTTP client with cookies and redirect support."""
        if self._http_client is None:
            self._http_client = httpx.Client(
                follow_redirects=True,
                cookies=httpx.Cookies()
            )
        return self._http_client

    @property
    def api(self) -> httpx.Client:
        """HTTP client with API headers."""
        client = self.http
        client.headers.update(self.headers)
        return client

    @property
    def headers(self) -> Dict[str, str]:
        """API request headers."""
        return {
            'User-Agent': 'Dropcountr Python Client',
            'Content-Type': 'application/json',
            'Accept': 'application/vnd.dropcountr.api+json;version=2',
        }

    def login(self) -> httpx.Response:
        """Authenticate with Dropcountr API."""
        return self.http.post(
            self.LOGIN_URL,
            data={'email': self.email, 'password': self.password}
        )

    def get(self, url: str) -> Any:
        """Make a GET request and extract data from response."""
        response = self.api.get(url)
        response.raise_for_status()
        return response.json()["data"]

    def logout(self) -> Any:
        """Logout from Dropcountr API."""
        return self.get(self.LOGOUT_URL)

    def me(self) -> Dict[str, Any]:
        """Get current user information."""
        return self.get(self.USER_DISCOVERY_API)

    def premise(self, url: str) -> Dict[str, Any]:
        """Get premise information."""
        return self.get(url)

    def service_connection(self, url: str) -> Dict[str, Any]:
        """Get service connection information."""
        return self.get(url)

    def usage(self, templated_url: str, period: str, during: str) -> Dict[str, Any]:
        """Get usage data for a given period and time range."""
        return self._series(templated_url=templated_url, period=period, during=during)

    def cost(self, templated_url: str, period: str, during: str) -> Dict[str, Any]:
        """Get cost data for a given period and time range."""
        return self._series(templated_url=templated_url, period=period, during=during)

    def goal(self, templated_url: str, period: str, during: str) -> Dict[str, Any]:
        """Get goal data for a given period and time range."""
        return self._series(templated_url=templated_url, period=period, during=during)

    def _series(self, templated_url: str, period: str, during: str) -> Dict[str, Any]:
        """
        Expand URI template with period and during parameters, then fetch data.
        
        Args:
            templated_url: URI template string (e.g., "https://api.example.com/{period}/{during}")
            period: Period identifier (e.g., "day", "week", "month")
            during: ISO8601 interval string with dates or timestamps (e.g., "2023-01-01/2023-01-31" or "2023-01-01T00:00:00Z/2023-01-31T23:59:59Z")
        """
        template = URITemplate(templated_url)
        expanded_url = template.expand(
            period=period,
            during=self._format_time_range(during)
        )
        return self.get(expanded_url)

    @staticmethod
    def _format_time_range(during: str) -> str:
        """
        Format time range to ISO8601 format.
        
        Accepts ISO8601 interval strings with dates or timestamps.
        Examples: 
            - Dates: "2023-01-01/2023-01-31"
            - Timestamps: "2023-01-01T00:00:00Z/2023-01-31T23:59:59Z"
            - Mixed: "2023-01-01/2023-01-31T23:59:59Z"
        """
        # If during is already in ISO8601 format, return as-is
        if isinstance(during, str) and '/' in during:
            return during
        
        # If it's a datetime range object or needs conversion, handle it here
        # For now, assume the input is already in the correct format
        return during

