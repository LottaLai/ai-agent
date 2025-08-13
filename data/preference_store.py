"""
User preference storage and management
"""

from typing import Any, Dict, List, Optional

# In-memory storage for user preferences
# In production, this should be replaced with a database
user_preferences: Dict[str, Dict[str, Any]] = {}


def get_user_pref(user_id: str) -> Dict[str, Any]:
    """
    Get user preferences

    Args:
        user_id: User identifier

    Returns:
        Dictionary containing user preferences
    """
    return user_preferences.get(
        user_id,
        {
            "favorite_cuisines": [],
            "dietary_restrictions": [],
            "price_range": "moderate",
            "distance_preference": "nearby",
            "rating_threshold": 3.5,
        },
    )


def update_user_pref(user_id: str, preferences: Dict[str, Any]) -> bool:
    """
    Update user preferences

    Args:
        user_id: User identifier
        preferences: Dictionary of preferences to update

    Returns:
        True if update successful, False otherwise
    """
    try:
        if user_id not in user_preferences:
            user_preferences[user_id] = {}

        user_preferences[user_id].update(preferences)
        return True
    except Exception:
        return False


def add_favorite_cuisine(user_id: str, cuisine: str) -> bool:
    """
    Add a cuisine to user's favorites

    Args:
        user_id: User identifier
        cuisine: Cuisine type to add

    Returns:
        True if added successfully
    """
    prefs = get_user_pref(user_id)
    if cuisine not in prefs.get("favorite_cuisines", []):
        prefs.setdefault("favorite_cuisines", []).append(cuisine)
        return update_user_pref(user_id, prefs)
    return True


def set_dietary_restrictions(user_id: str, restrictions: List[str]) -> bool:
    """
    Set dietary restrictions for user

    Args:
        user_id: User identifier
        restrictions: List of dietary restrictions

    Returns:
        True if set successfully
    """
    return update_user_pref(user_id, {"dietary_restrictions": restrictions})


def get_favorite_cuisines(user_id: str) -> List[str]:
    """
    Get user's favorite cuisines

    Args:
        user_id: User identifier

    Returns:
        List of favorite cuisines
    """
    prefs = get_user_pref(user_id)
    return prefs.get("favorite_cuisines", [])
