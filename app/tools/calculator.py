from datetime import date, timedelta


def calculate_working_days(start_date: str, end_date: str) -> dict:
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError as e:
        return {"error": f"Invalid date format: {e}. Use YYYY-MM-DD."}

    if end < start:
        return {"error": "end_date must be on or after start_date"}

    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5:  # Mon–Fri
            count += 1
        current += timedelta(days=1)

    return {"start_date": start_date, "end_date": end_date, "working_days": count}
