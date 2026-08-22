#!/usr/bin/env python3
"""
Example usage of the Dropcountr Python client.

Before running this script:
1. Install dependencies: pip install -r requirements.txt
2. Create a .env file with DROPCOUNTR_EMAIL and DROPCOUNTR_PASS

This will:
- Login and display user info
- Fetch all premises and their meters
- Display usage data (gallons, leak detection) for the last 3 days
- Display cost data with detailed breakdowns
- Display leaks for each service connection over the same window
"""

from dotenv import load_dotenv
load_dotenv()

from dropcountr import DropcountrClient
import os
import sys
from datetime import datetime, timedelta, date


def format_iso8601_range(start_date, end_date):
    """Format an exclusive-ended ISO8601 interval (end not included)."""
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
    if not os.environ.get('DROPCOUNTR_EMAIL') or not os.environ.get('DROPCOUNTR_PASS'):
        print("Error: DROPCOUNTR_EMAIL and DROPCOUNTR_PASS must be set in environment")
        sys.exit(1)

    client = DropcountrClient(
        email=os.environ['DROPCOUNTR_EMAIL'],
        password=os.environ['DROPCOUNTR_PASS']
    )

    client.login()

    user = client.me()
    print(f"Hi {user.name}")

    premises = [client.premise(ref.id) for ref in user.premises]

    for premise in premises:
        print(f"Premise: {premise.name}, meters: {len(premise.service_connections)}")

    during_start = datetime.now() - timedelta(days=3)
    during_end = date.today()
    during = format_iso8601_range(during_start, during_end)
    period = "day"

    for premise in premises:
        print(f"\nPremise: {premise.name}")

        for sc in premise.service_connections:
            print(f"SC: {sc.id}, Meter ID: {sc.meter_id}")

            if not sc.usage_series or not sc.cost_series:
                continue

            usages = client.usage(
                templated_url=sc.usage_series.template,
                period=period,
                during=during,
            )
            for day in usages.members:
                print(f"Day: {day.during}")
                print(f"\t Total: {day.total_gallons}, Leaking?: {day.is_leaking}")

            costs = client.cost(
                templated_url=sc.cost_series.template,
                period=period,
                during=during,
            )
            for day in costs.members:
                price = round(day.price, 2)
                print(f"Day: {day.during}")
                print(f"\t Total Price: {price}, Currency: {day.price_currency}")
                for cost_item in day.items:
                    item_price = round(cost_item.price, 2)
                    print(f"\t\t{cost_item.name}, price: {item_price}")

            if not sc.leaks:
                continue

            leak_series = client.leaks(
                templated_url=sc.leaks.template,
                during=during,
            )
            print(f"Leaks ({leak_series.total_items}):")
            for summary in leak_series.members:
                leak = client.leak(summary.id)
                volume = leak.est_total_volume
                hourly = leak.est_hourly_volume
                cost = leak.est_total_cost
                print(f"\t Leak: {leak.id}")
                print(f"\t\t Via meter: {leak.via.id if leak.via else None}")
                print(f"\t\t Started: {leak.started_at}, Resolved: {leak.resolved_at}")
                print(
                    f"\t\t Volume: {volume.value if volume else None} "
                    f"{volume.unit_code if volume else ''}".rstrip()
                )
                print(
                    f"\t\t Hourly: {hourly.value if hourly else None} "
                    f"{hourly.unit_code if hourly else ''}".rstrip()
                )
                print(
                    f"\t\t Est. cost: "
                    f"{round(cost.price, 2) if cost else None} "
                    f"{cost.price_currency if cost else ''}".rstrip()
                )
                print(
                    f"\t\t Ignored: {leak.is_ignored}, "
                    f"Archived: {leak.is_archived}, "
                    f"Snoozed until: {leak.snoozed_until}"
                )

                comps = client.leak_usage_comps(leak, period=period, during=during)
                print(f"\t\t Usage comps ({comps.total_items}):")
                for point in comps.members:
                    actual = point.actual_usage.value if point.actual_usage else None
                    expected = (
                        point.expected_usage.value if point.expected_usage else None
                    )
                    print(
                        f"\t\t\t {point.during}: "
                        f"actual={actual}, expected={expected}"
                    )

    client.logout()


if __name__ == "__main__":
    main()
