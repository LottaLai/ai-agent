"""
Meal period detection utilities
"""

from datetime import datetime


def get_meal_period(time_str: str) -> str:
    """
    Determine meal period based on time

    Args:
        time_str: Time string in format "YYYY-MM-DD HH:MM:SS"

    Returns:
        Meal period: "breakfast", "lunch", "dinner", or "snack"
    """
    try:
        # Parse time string
        if isinstance(time_str, str):
            time_obj = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        else:
            time_obj = datetime.now()

        hour = time_obj.hour

        # Define meal periods
        if 6 <= hour < 11:
            return "breakfast"
        elif 11 <= hour < 14:
            return "lunch"
        elif 14 <= hour < 17:
            return "afternoon_snack"
        elif 17 <= hour < 22:
            return "dinner"
        else:
            return "late_snack"

    except Exception:
        # Default to current time if parsing fails
        return get_meal_period(datetime.now().isoformat())


def is_meal_time(time_str: str, meal_type: str) -> bool:
    """
    Check if given time matches a specific meal period

    Args:
        time_str: Time string
        meal_type: Target meal type to check

    Returns:
        True if time matches the meal type
    """
    current_period = get_meal_period(time_str)
    return current_period == meal_type


def get_next_meal_time(current_time_str: str) -> tuple[str, str]:
    """
    Get the next meal period and its typical time

    Args:
        current_time_str: Current time string

    Returns:
        Tuple of (next_meal_type, suggested_time)
    """
    try:
        time_obj = datetime.fromisoformat(current_time_str.replace("Z", "+00:00"))
        hour = time_obj.hour

        if hour < 6:
            return ("breakfast", "07:00")
        elif hour < 11:
            return ("lunch", "12:00")
        elif hour < 14:
            return ("dinner", "18:00")
        elif hour < 17:
            return ("dinner", "18:00")
        elif hour < 22:
            return ("late_snack", "21:00")
        else:
            # Next day breakfast
            return ("breakfast", "07:00")

    except Exception:
        return ("lunch", "12:00")
