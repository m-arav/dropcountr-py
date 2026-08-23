# Dropcountr Python Client

A Python client library for the Dropcountr API, providing easy access to water usage, cost, and goal data.

## Installation

```bash
pip install dropcountr-py
```

Or from a local checkout:

```bash
pip install -e .
# optional example deps
pip install -e ".[examples]"
# or
pip install -r requirements.txt
```

## Dependencies

- **httpx**: Modern HTTP client with cookie and redirect support
- **uritemplate**: RFC 6570 URI Template expansion per the Python Hyper project
- **python-dotenv**: Environment variable management

## Quick Start

### Setup Environment Variables

1. Copy the example environment file:
```bash
cp env.example .env
```

2. Edit `.env` and add your credentials:
```bash
DROPCOUNTR_EMAIL=your_email@example.com
DROPCOUNTR_PASS=your_password
```

### Run the Example

```bash
python example.py
```

This will:
- Login and display user info
- Fetch all premises and their meters
- Display usage data (gallons, leak detection) for the last 3 days
- Display cost data with detailed breakdowns

## Usage

### Basic Authentication and User Info

```python
from dropcountr import DropcountrClient

# Create client instance
client = DropcountrClient(
    email="your_email@example.com",
    password="your_password"
)

# Login
client.login()

# Get user information
user_info = client.me()
print(user_info)

# Logout when done
client.logout()
```

### Context Manager (Recommended)

```python
from dropcountr import DropcountrClient

with DropcountrClient(email="your_email@example.com", password="your_password") as client:
    client.login()
    user_info = client.me()
    print(user_info)
    # Client automatically closes when exiting context
```

### Fetching Data

```python
# Get premise information
premise_data = client.premise("https://dropcountr.com/api/premises/123")

# Get service connection
connection_data = client.service_connection("https://dropcountr.com/api/service_connections/456")
```

### Time Series Data

Pass the service connection from a premise so timestamps are rewritten into
that premise's timezone (see [Timezones](#timezones)):

```python
premise = client.premise("https://dropcountr.com/api/premises/123")
sc = premise.service_connections[0]

usage_data = client.usage(sc, period="day", during="2023-01-01/2023-01-31")
cost_data = client.cost(sc, period="month", during="2023-01-01/2023-12-31")
goal_data = client.goal(sc, period="week", during="2023-01-01/2023-01-07")
```

A raw IRI template still works. Pass `premise=` (or `timezone=`) if you want
the same correction:

```python
client.usage(
    sc.usage_series.template,
    period="day",
    during="2023-01-01/2023-01-31",
    premise=premise,
)
```

### Timezones

Dropcountr returns usage, cost, goal, and leak times in the **premise's local
timezone**, but labels them as UTC (`Z` or `+00:00`). That is an API bug: a
Pacific day starting at local midnight arrives as `2023-01-01T00:00:00Z`, which
parsers treat as UTC midnight (4–8 hours off).

This client keeps the wall-clock time and attaches the real offset for the
premise. The IANA zone comes from the premise address (US state, refined with
lat/lng when the state spans more than one zone) — not from `User.timezone`,
which is a profile setting and can differ from where the meter is.

```text
API:     2023-08-01T00:00:00Z/2023-08-02T00:00:00Z
Client:  2023-08-01T00:00:00-07:00/2023-08-02T00:00:00-07:00
         (America/Los_Angeles, PDT)
```

`Premise.timezone` is filled when the premise is parsed. Service connections
embedded on that payload get the same zone, so `client.usage(sc, ...)` can
correct timestamps without an extra argument.

## API Methods

### Authentication
- `login()`: Authenticate with the Dropcountr API
- `logout()`: End the current session
- `me()`: Get current user information

### Data Access
- `premise(url)`: Fetch premise data
- `service_connection(url)`: Fetch service connection data
- `usage(source, period, during, *, premise=None, timezone=None)`: Fetch usage time series
- `cost(source, period, during, *, premise=None, timezone=None)`: Fetch cost time series
- `goal(source, period, during, *, premise=None, timezone=None)`: Fetch goal time series
- `leaks(source, during, *, premise=None, timezone=None)`: Fetch leaks for a meter
- `leak(url, *, premise=None, timezone=None)`: Fetch one leak
- `leak_usage_comps(leak, period, during, *, premise=None, timezone=None)`: Fetch leak usage comps

`source` is a `ServiceConnection` (preferred — uses the premise timezone stamped on it) or an IRI template string.

### Parameters

#### Period
- `"hour"`: Hourly data
- `"day"`: Daily data
- `"week"`: Weekly data
- `"month"`: Monthly data
- `"billing"`: Billing-period data — only when the `billing_period` feature flag is set on the service connection

#### During
Exclusive-ended ISO8601 interval (`start/end`). The end instant is **not** included.

- Format: `"start_time/end_time"`
- Example: `"2023-01-01/2023-01-04"` covers Jan 1–3
