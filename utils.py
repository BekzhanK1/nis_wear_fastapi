from datetime import datetime, timedelta


def get_next_shipping_day(order_date: datetime) -> datetime:
    """
    Calculate the next shipping Sunday, which occurs every two weeks starting from a known date.
    If the order is placed on a shipping day (Sunday), the order is moved to the next shipping day (two weeks later).
    """
    order_date = order_date + timedelta(days=2)
    # Define the known start date for the shipping cycle (e.g., 2024-09-08)
    start_date = datetime(2024, 9, 8)  # A known shipping Sunday

    # Get the current day of the week (0=Monday, 6=Sunday)
    days_until_sunday = (6 - order_date.weekday()) % 7

    # Get the upcoming Sunday
    next_sunday = order_date + timedelta(days=days_until_sunday)

    # Calculate the number of days since the start date
    days_since_start = (next_sunday - start_date).days

    # If the order date is on a shipping Sunday, move to the next shipping Sunday
    if days_since_start % 14 == 0 and next_sunday == order_date:
        # Today is already a shipping Sunday, so move to the next shipping Sunday (2 weeks later)
        return next_sunday + timedelta(weeks=2)
    elif days_since_start % 14 == 0:
        # Next Sunday is a shipping Sunday
        return next_sunday
    else:
        # Otherwise, move to the next valid shipping Sunday (add the remaining days to reach the next cycle)
        return next_sunday + timedelta(weeks=1)
