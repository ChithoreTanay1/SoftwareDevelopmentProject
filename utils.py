"""
Utility functions for the Kahoot-style quiz application.
Common helper functions and decorators.
"""

import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
import logging

logger = logging.getLogger(__name__)


def generate_unique_id() -> str:
    """Generate a unique identifier."""
    return str(uuid.uuid4())


def generate_room_code(length: int = 6) -> str:
    """Generate a random room code."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))


def calculate_time_bonus(response_time: float, time_limit: int, max_bonus: float = 0.2) -> float:
    """
    Calculate time bonus for quick answers.
    
    Args:
        response_time: Time taken to answer in seconds
        time_limit: Total time allowed for the question
        max_bonus: Maximum bonus percentage (0.2 = 20% bonus)
    
    Returns:
        Bonus multiplier (0.0 to max_bonus)
    """
    if response_time >= time_limit:
        return 0.0
    
    # Linear bonus: faster answers get higher bonus
    remaining_time = time_limit - response_time
    time_ratio = remaining_time / time_limit
    return min(time_ratio * max_bonus, max_bonus)


def calculate_score(base_points: int, is_correct: bool, response_time: Optional[float] = None, 
                   time_limit: int = 30) -> int:
    """
    Calculate final score for a question answer.
    
    Args:
        base_points: Base points for the question
        is_correct: Whether the answer is correct
        response_time: Time taken to answer (optional)
        time_limit: Time limit for the question
    
    Returns:
        Final score
    """
    if not is_correct:
        return 0
    
    if response_time is None:
        return base_points
    
    time_bonus = calculate_time_bonus(response_time, time_limit)
    final_score = int(base_points * (1 + time_bonus))
    return final_score


def sanitize_nickname(nickname: str) -> str:
    """
    Sanitize player nickname for display.
    
    Args:
        nickname: Raw nickname input
    
    Returns:
        Sanitized nickname
    """
    # Remove leading/trailing whitespace
    nickname = nickname.strip()
    
    # Limit length
    if len(nickname) > 100:
        nickname = nickname[:100]
    
    # Replace empty with default
    if not nickname:
        nickname = f"Player{random.randint(1000, 9999)}"
    
    return nickname


def format_time_remaining(start_time: datetime, time_limit: int) -> int:
    """
    Calculate remaining time for a question.
    
    Args:
        start_time: When the question started
        time_limit: Total time allowed in seconds
    
    Returns:
        Remaining seconds (0 if time expired)
    """
    elapsed = (datetime.utcnow() - start_time).total_seconds()
    remaining = max(0, time_limit - int(elapsed))
    return remaining


def validate_choice_distribution(choices: list) -> Dict[str, Any]:
    """
    Validate choice distribution for a question.
    
    Args:
        choices: List of choice objects
    
    Returns:
        Validation result with status and message
    """
    if len(choices) < 2:
        return {"valid": False, "message": "At least 2 choices required"}
    
    if len(choices) > 4:
        return {"valid": False, "message": "Maximum 4 choices allowed"}
    
    correct_choices = [c for c in choices if c.is_correct]
    if len(correct_choices) == 0:
        return {"valid": False, "message": "At least one correct choice required"}
    
    # For multiple choice, typically only one correct answer
    if len(correct_choices) > 1:
        logger.warning(f"Multiple correct choices detected: {len(correct_choices)}")
    
    return {"valid": True, "message": "Choices are valid"}


class GameState:
    """Helper class to track game state transitions."""
    
    WAITING = "waiting"
    ACTIVE = "active" 
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    
    VALID_TRANSITIONS = {
        WAITING: [ACTIVE, CANCELLED],
        ACTIVE: [COMPLETED, CANCELLED],
        COMPLETED: [],
        CANCELLED: []
    }
    
    @classmethod
    def can_transition(cls, from_state: str, to_state: str) -> bool:
        """Check if state transition is valid."""
        return to_state in cls.VALID_TRANSITIONS.get(from_state, [])


def log_performance(func_name: str, start_time: datetime, **kwargs):
    """Log performance metrics for functions."""
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    if duration > 1.0:  # Log slow operations
        logger.warning(f"Slow operation: {func_name} took {duration:.2f}s", extra=kwargs)
    elif duration > 0.5:
        logger.info(f"Operation: {func_name} took {duration:.2f}s", extra=kwargs)


def paginate_results(items: list, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
    """
    Paginate a list of items.
    
    Args:
        items: List of items to paginate
        page: Page number (1-based)
        per_page: Items per page
    
    Returns:
        Paginated result with metadata
    """
    total_items = len(items)
    total_pages = (total_items + per_page - 1) // per_page
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    paginated_items = items[start_idx:end_idx]
    
    return {
        "items": paginated_items,
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }