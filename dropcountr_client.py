import httpx
from uritemplate import URITemplate
from typing import Any, Dict, Optional

from models import (
    CostSeries,
    GoalSeries,
    Leak,
    LeakSeries,
    LeakUsageCompSeries,
    Premise,
    ServiceConnection,
    UsageSeries,
    User,
)


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

    def me(self) -> User:
        """Get current user information."""
        return User.from_dict(self.get(self.USER_DISCOVERY_API))

    def premise(self, url: str) -> Premise:
        """Get premise information."""
        return Premise.from_dict(self.get(url))

    def service_connection(self, url: str) -> ServiceConnection:
        """Get service connection information."""
        return ServiceConnection.from_dict(self.get(url))

    def usage(self, templated_url: str, period: str, during: str) -> UsageSeries:
        """Get usage data for a given period and exclusive-ended time range."""
        return UsageSeries.from_dict(
            self._series(templated_url=templated_url, period=period, during=during)
        )

    def cost(self, templated_url: str, period: str, during: str) -> CostSeries:
        """Get cost data for a given period and exclusive-ended time range."""
        return CostSeries.from_dict(
            self._series(templated_url=templated_url, period=period, during=during)
        )

    def goal(self, templated_url: str, period: str, during: str) -> GoalSeries:
        """Get goal data for a given period and exclusive-ended time range."""
        return GoalSeries.from_dict(
            self._series(templated_url=templated_url, period=period, during=during)
        )

    def leaks(self, templated_url: str, during: str) -> LeakSeries:
        """Get leaks for a service connection over an exclusive-ended time range.

        Uses the meter's ``leaks`` IRI template (``{?during}`` only).
        """
        template = URITemplate(templated_url)
        expanded_url = template.expand(during=self._format_time_range(during))
        return LeakSeries.from_dict(self.get(expanded_url))

    def leak(self, url: str) -> Leak:
        """Get a single leak by resource URL."""
        return Leak.from_dict(self.get(url))

    def leak_usage_comps(
        self, leak: Leak, period: str, during: str
    ) -> LeakUsageCompSeries:
        """Get actual vs expected usage for a leak over an exclusive-ended range.

        Expands the leak's ``usage_comp_series`` template
        (``{?during,period}``).
        """
        if not leak.usage_comp_series:
            raise ValueError(f"Leak {leak.id} has no usage_comp_series template")
        return LeakUsageCompSeries.from_dict(
            self._series(
                templated_url=leak.usage_comp_series.template,
                period=period,
                during=during,
            )
        )

    def _series(self, templated_url: str, period: str, during: str) -> Dict[str, Any]:
        """
        Expand URI template with period and during parameters, then fetch data.

        Args:
            templated_url: URI template string (e.g. usage{?during,period})
            period: One of hour, day, week, month, billing.
                ``billing`` requires the ``billing_period`` feature flag.
            during: Exclusive-ended ISO8601 interval ``start/end``
                (end is excluded). Example: ``2023-01-01/2023-01-04`` covers
                Jan 1–3.
        """
        template = URITemplate(templated_url)
        expanded_url = template.expand(
            period=period,
            during=self._format_time_range(during),
        )
        return self.get(expanded_url)

    @staticmethod
    def _format_time_range(during: str) -> str:
        """
        Pass through an exclusive-ended ISO8601 interval.

        Accepts ``start/end`` with dates or timestamps. The end instant is
        exclusive. Examples:
            - Dates: "2023-01-01/2023-01-04"  (covers Jan 1–3)
            - Timestamps: "2023-01-01T00:00:00Z/2023-01-04T00:00:00Z"
        """
        if isinstance(during, str) and '/' in during:
            return during
        return during
