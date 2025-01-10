from datetime import datetime, timedelta
    
def adjust_week(week_str, delta_weeks):
    year, week = map(int, week_str.split('-W'))
    start_of_week = datetime.fromisocalendar(year, week, 1)
    adjusted_date = start_of_week + timedelta(weeks=delta_weeks)
    adjusted_year, adjusted_week, _ = adjusted_date.isocalendar()
    adjusted_week_str = f"{adjusted_year}-W{adjusted_week:02d}"
    return adjusted_week_str

def add_days(date_str, days, date_format="%Y-%m-%d"):
    # Convert the string to a datetime object
    dt = datetime.strptime(date_str, date_format)
    # Add the specified number of days
    new_date = dt + timedelta(days=days)
    # Convert back to string if needed, or return the datetime object
    return new_date.strftime(date_format)



def calculate_current_iso_week(date_str):
    # Get the current date
    current_date = datetime.strptime(date_str, "%Y-%m-%d")

    # Determine if current day is Saturday (5) or Sunday (6)
    if current_date.weekday() == 5 or current_date.weekday() == 6:
        # Move to Monday of next week
        days_till_next_monday = 7 - current_date.weekday()
        current_date += timedelta(days=days_till_next_monday)

    # Calculate the start and end of the current ISO week
    # ISO weeks start on Monday and end on Sunday
    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # Get ISO calendar info
    year, week_number, _ = current_date.isocalendar()

    # Pad the week number with leading zero if necessary
    week_number_str = f"{week_number:02d}"

    # Combine into the full string
    week_range_str = f"{year}-W{week_number_str}"

    return week_range_str