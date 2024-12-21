# File: /backend/utils/error_handlers.py

from typing import Dict, Any, Optional
from pydantic import BaseModel, ValidationError
from fastapi import HTTPException, status
import traceback
from .logger import logger

class ErrorResponse(BaseModel):
    """Standardized error response"""
    error: str
    detail: Optional[str] = None
    code: str
    status_code: int = 400

class ScrapingError(Exception):
    """Custom exception for scraping errors"""
    def __init__(self, message: str, code: str = "SCRAPING_ERROR", status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)

def handle_error(error: Exception) -> Dict[str, Any]:
    """Central error handler for all API endpoints"""
    if isinstance(error, ValidationError):
        return ErrorResponse(
            error="Validation error",
            detail=str(error),
            code="VALIDATION_ERROR",
            status_code=422
        ).dict()
        
    if isinstance(error, ScrapingError):
        return ErrorResponse(
            error=error.message,
            code=error.code,
            status_code=error.status_code
        ).dict()

    if isinstance(error, HTTPException):
        return ErrorResponse(
            error=error.detail,
            code="HTTP_ERROR",
            status_code=error.status_code
        ).dict()

    # Log unexpected errors
    logger.error(
        "Unexpected error",
        extra={
            'error_type': error.__class__.__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        }
    )

    return ErrorResponse(
        error="Internal server error",
        detail=str(error) if str(error) else None,
        code="INTERNAL_ERROR",
        status_code=500
    ).dict()

def validate_scraping_request(data: Dict) -> Optional[str]:
    """Validate scraping request parameters"""
    required_fields = ['query']
    for field in required_fields:
        if field not in data:
            return f"Missing required field: {field}"

    # Validate platform
    if platform := data.get('platform'):
        if platform not in ['ebay', 'amazon']:
            return f"Invalid platform: {platform}"

    # Validate max_items
    if max_items := data.get('max_items'):
        try:
            max_items = int(max_items)
            if max_items < 1 or max_items > 200:
                return "max_items must be between 1 and 200"
        except ValueError:
            return "max_items must be a number"

    # Validate price filters
    if filters := data.get('filters', {}):
        if price_min := filters.get('price_min'):
            try:
                price_min = float(price_min)
                if price_min < 0:
                    return "price_min cannot be negative"
            except ValueError:
                return "price_min must be a number"

        if price_max := filters.get('price_max'):
            try:
                price_max = float(price_max)
                if price_max < 0:
                    return "price_max cannot be negative"
            except ValueError:
                return "price_max must be a number"

        if price_min and price_max and price_min > price_max:
            return "price_min cannot be greater than price_max"

    return None

def sanitize_input(value: str) -> str:
    """Sanitize user input"""
    # Remove potentially harmful characters
    sanitized = ''.join(char for char in value if char.isprintable())
    # Limit length
    return sanitized[:500]

class RequestTracker:
    """Track and manage API request patterns"""
    
    def __init__(self):
        self.requests: Dict[str, Dict] = {}
        self._cleanup_threshold = 1000

    def track_request(self, ip: str, endpoint: str, status_code: int):
        """Track request details"""
        if len(self.requests) > self._cleanup_threshold:
            self._cleanup_old_requests()

        if ip not in self.requests:
            self.requests[ip] = {
                'count': 0,
                'errors': 0,
                'last_request': datetime.now(),
                'endpoints': {}
            }

        self.requests[ip]['count'] += 1
        self.requests[ip]['last_request'] = datetime.now()
        
        if status_code >= 400:
            self.requests[ip]['errors'] += 1

        # Track endpoint usage
        if endpoint not in self.requests[ip]['endpoints']:
            self.requests[ip]['endpoints'][endpoint] = 0
        self.requests[ip]['endpoints'][endpoint] += 1

    def _cleanup_old_requests(self):
        """Remove old request data"""
        threshold = datetime.now() - timedelta(hours=1)
        self.requests = {
            ip: data for ip, data in self.requests.items()
            if data['last_request'] > threshold
        }

    def get_client_stats(self, ip: str) -> Dict:
        """Get statistics for client"""
        if ip not in self.requests:
            return {}

        data = self.requests[ip]
        return {
            'total_requests': data['count'],
            'error_rate': data['errors'] / data['count'] if data['count'] > 0 else 0,
            'last_request': data['last_request'].isoformat(),
            'endpoint_usage': data['endpoints']
        }

# Initialize request tracker
request_tracker = RequestTracker()