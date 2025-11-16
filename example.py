#!/usr/bin/env python3
"""
Example usage of the Dropcountr Python client.

Before running this script:
1. Install dependencies: pip install -r requirements.txt
2. Create a .env file with DROPCOUNTR_EMAIL and DROPCOUNTR_PASS
"""

from dotenv import load_dotenv
load_dotenv()

from dropcountr_client import DropcountrClient
import os
import sys
from datetime import datetime, timedelta, date


def format_iso8601_range(start_date, end_date):
    """Format date range as ISO8601 interval (e.g., '2023-01-01/2023-01-03')."""
    if isinstance(start_date, datetime):
        start_str = start_date.strftime('%Y-%m-%d')
    else:
        start_str = str(start_date)
    
    if isinstance(end_date, datetime):
        end_str = end_date.strftime('%Y-%m-%d')
    else:
        end_str = str(end_date)
    
    return f"{start_str}/{end_str}"


def main():
    # Ensure environment variables are set
    if not os.environ.get('DROPCOUNTR_EMAIL') or not os.environ.get('DROPCOUNTR_PASS'):
        print("Error: DROPCOUNTR_EMAIL and DROPCOUNTR_PASS must be set in environment")
        sys.exit(1)

    client = DropcountrClient(
        email=os.environ['DROPCOUNTR_EMAIL'],
        password=os.environ['DROPCOUNTR_PASS']
    )

    # Login
    client.login()

    # Fetch user data
    user = client.me()
    print(f"Hi {user['name']}")

    # Load premise information
    premises = [
        client.premise(premise['@id'])
        for premise in user['premises']
    ]

    for premise in premises:
        service_connections_count = len(premise['service_connections'])
        print(f"Premise: {premise['name']}, meters: {service_connections_count}")

    # Load usage, cost, goal data for all meters for last 3 days
    during_start = datetime.now() - timedelta(days=3)
    during_end = date.today()
    during = format_iso8601_range(during_start, during_end)
    period = "day"  # month, hour

    for premise in premises:
        print(f"\nPremise: {premise['name']}")
        
        for sc in premise['service_connections']:
            print(f"SC: {sc['@id']}, Meter ID: {sc['meter_id']}")

            # Fetch usage data
            usage_url = sc['usage_series']['template']
            usages = client.usage(templated_url=usage_url, period=period, during=during)
            
            for day in usages['member']:
                print(f"Day: {day['during']}")
                print(f"\t Total: {day['total_gallons']}, Leaking?: {day['is_leaking']}")

            # Fetch cost data
            cost_url = sc['cost_series']['template']
            costs = client.cost(templated_url=cost_url, period=period, during=during)
            
            for day in costs['member']:
                price = round(float(day.get('price') or 0.0), 2)
                print(f"Day: {day['during']}")
                print(f"\t Total Price: {price}, Currency: {day['priceCurrency']}")
                
                # Show cost split
                for cost_item in day['items']:
                    item_price = round(float(cost_item.get('price') or 0.0), 2)
                    print(f"\t\t{cost_item['name']}, price: {item_price}")

    client.logout()


if __name__ == "__main__":
    main()

