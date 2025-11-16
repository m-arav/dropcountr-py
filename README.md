# Dropcountr Python Client

A Python client library for the Dropcountr API, providing easy access to water usage, cost, and goal data.

## Installation

### Quick Install (with existing Python environment)

```bash
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
from dropcountr_client import DropcountrClient

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
from dropcountr_client import DropcountrClient

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

```python
# Usage data
usage_data = client.usage(
    templated_url="https://dropcountr.com/api/usage{/period}{/during}",
    period="day",
    during="2023-01-01/2023-01-31"
)

# Cost data
cost_data = client.cost(
    templated_url="https://dropcountr.com/api/cost{/period}{/during}",
    period="month",
    during="2023-01-01/2023-12-31"
)

# Goal data
goal_data = client.goal(
    templated_url="https://dropcountr.com/api/goals{/period}{/during}",
    period="week",
    during="2023-01-01/2023-01-07"
)
```

## API Methods

### Authentication
- `login()`: Authenticate with the Dropcountr API
- `logout()`: End the current session
- `me()`: Get current user information

### Data Access
- `premise(url)`: Fetch premise data
- `service_connection(url)`: Fetch service connection data
- `usage(templated_url, period, during)`: Fetch usage time series
- `cost(templated_url, period, during)`: Fetch cost time series
- `goal(templated_url, period, during)`: Fetch goal time series

### Parameters

#### Period
Common period values:
- `"hour"`: Hour Data
- `"day"`: Daily data
- `"month"`: Monthly data

#### During
Time range in ISO8601 interval format:
- Format: `"start_time/end_time"`
- Example: `"2023-01-01/2023-01-31"`
