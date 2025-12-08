

from typing import Optional, Any, Dict


class QuizGameException(Exception):
    """Base exception for quiz game errors."""
    
    def __init__(self, message: str, error_code: str = "QUIZ_GAME_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(QuizGameException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, invalid_value: Any = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field
        self.invalid_value = invalid_value


class ResourceNotFoundException(QuizGameException):
    """Exception for resource not found errors."""
    
    def __init__(self, resource_type: str, identifier: str):
        message = f"{resource_type} not found: {identifier}"
        super().__init__(message, "RESOURCE_NOT_FOUND", {
            "resource_type": resource_type,
            "identifier": identifier
        })
        self.resource_type = resource_type
        self.identifier = identifier


class QuizNotFoundException(ResourceNotFoundException):
    """Exception for quiz not found errors."""
    
    def __init__(self, quiz_id: str):
        super().__init__("Quiz", quiz_id)


class RoomNotFoundException(ResourceNotFoundException):
    """Exception for room not found errors."""
    
    def __init__(self, room_code: str):
        super().__init__("Room", room_code)


class PlayerNotFoundException(ResourceNotFoundException):
    """Exception for player not found errors."""
    
    def __init__(self, player_id: str):
        super().__init__("Player", player_id)


class QuestionNotFoundException(ResourceNotFoundException):
    """Exception for question not found errors."""
    
    def __init__(self, question_id: str):
        super().__init__("Question", question_id)


class GameStateException(QuizGameException):
    """Exception for invalid game state operations."""
    
    def __init__(self, operation: str, current_state: str, required_state: str):
        message = f"Cannot {operation} in state '{current_state}'. Required state: '{required_state}'"
        super().__init__(message, "INVALID_GAME_STATE", {
            "operation": operation,
            "current_state": current_state,
            "required_state": required_state
        })
        self.operation = operation
        self.current_state = current_state
        self.required_state = required_state


class RoomFullException(QuizGameException):
    """Exception for room capacity exceeded."""
    
    def __init__(self, room_code: str, max_players: int):
        message = f"Room {room_code} is full (max {max_players} players)"
        super().__init__(message, "ROOM_FULL", {
            "room_code": room_code,
            "max_players": max_players
        })
        self.room_code = room_code
        self.max_players = max_players


class DuplicatePlayerException(QuizGameException):
    """Exception for duplicate player in room."""
    
    def __init__(self, player_id: str, room_code: str):
        message = f"Player {player_id} already exists in room {room_code}"
        super().__init__(message, "DUPLICATE_PLAYER", {
            "player_id": player_id,
            "room_code": room_code
        })
        self.player_id = player_id
        self.room_code = room_code


class DuplicateAnswerException(QuizGameException):
    """Exception for duplicate answer submission."""
    
    def __init__(self, player_id: str, question_id: str):
        message = f"Player {player_id} has already answered question {question_id}"
        super().__init__(message, "DUPLICATE_ANSWER", {
            "player_id": player_id,
            "question_id": question_id
        })
        self.player_id = player_id
        self.question_id = question_id


class InvalidAnswerException(QuizGameException):
    """Exception for invalid answer submission."""
    
    def __init__(self, reason: str, player_id: str, question_id: str):
        message = f"Invalid answer from player {player_id} for question {question_id}: {reason}"
        super().__init__(message, "INVALID_ANSWER", {
            "reason": reason,
            "player_id": player_id,
            "question_id": question_id
        })
        self.reason = reason
        self.player_id = player_id
        self.question_id = question_id


class QuizCreationException(QuizGameException):
    """Exception for quiz creation errors."""
    
    def __init__(self, reason: str):
        message = f"Failed to create quiz: {reason}"
        super().__init__(message, "QUIZ_CREATION_ERROR", {"reason": reason})
        self.reason = reason


class DatabaseException(QuizGameException):
    """Exception for database operation errors."""
    
    def __init__(self, operation: str, error: str):
        message = f"Database error during {operation}: {error}"
        super().__init__(message, "DATABASE_ERROR", {
            "operation": operation,
            "error": error
        })
        self.operation = operation
        self.error = error


class WebSocketException(QuizGameException):
    """Exception for WebSocket operation errors."""
    
    def __init__(self, operation: str, reason: str):
        message = f"WebSocket error during {operation}: {reason}"
        super().__init__(message, "WEBSOCKET_ERROR", {
            "operation": operation,
            "reason": reason
        })
        self.operation = operation
        self.reason = reason


class AuthorizationException(QuizGameException):
    """Exception for authorization errors."""
    
    def __init__(self, action: str, resource: str):
        message = f"Not authorized to {action} {resource}"
        super().__init__(message, "AUTHORIZATION_ERROR", {
            "action": action,
            "resource": resource
        })
        self.action = action
        self.resource = resource


class RateLimitException(QuizGameException):
    """Exception for rate limiting errors."""
    
    def __init__(self, action: str, retry_after: int):
        message = f"Rate limit exceeded for {action}. Retry after {retry_after} seconds"
        super().__init__(message, "RATE_LIMIT_EXCEEDED", {
            "action": action,
            "retry_after": retry_after
        })
        self.action = action
        self.retry_after = retry_after


class ConfigurationException(QuizGameException):
    """Exception for configuration errors."""
    
    def __init__(self, setting: str, reason: str):
        message = f"Configuration error for {setting}: {reason}"
        super().__init__(message, "CONFIGURATION_ERROR", {
            "setting": setting,
            "reason": reason
        })
        self.setting = setting
        self.reason = reason


# ============================================================================
# EXCEPTION MAPPING FOR HTTP STATUS CODES
# ============================================================================

EXCEPTION_STATUS_MAP = {
    QuizGameException: 500,
    ValidationException: 400,
    ResourceNotFoundException: 404,
    QuizNotFoundException: 404,
    RoomNotFoundException: 404,
    PlayerNotFoundException: 404,
    QuestionNotFoundException: 404,
    GameStateException: 400,
    RoomFullException: 409,
    DuplicatePlayerException: 409,
    DuplicateAnswerException: 409,
    InvalidAnswerException: 400,
    QuizCreationException: 400,
    DatabaseException: 500,
    WebSocketException: 500,
    AuthorizationException: 403,
    RateLimitException: 429,
    ConfigurationException: 500,
}


def get_http_status_code(exception: Exception) -> int:
    """Get HTTP status code for an exception."""
    return EXCEPTION_STATUS_MAP.get(type(exception), 500)


def format_error_response(exception: QuizGameException) -> dict:
    """Format exception as error response."""
    return {
        "success": False,
        "message": exception.message,
        "error_code": exception.error_code,
        "details": exception.details
    }
