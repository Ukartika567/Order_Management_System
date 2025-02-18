import logging
import json

# Configure logger
logger = logging.getLogger("api_logger")

class RequestResponseLoggingMiddleware:
    """Middleware to log API requests and responses"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/oms/"):
            logger.info(f" Request: {request.method} {request.path}")
            
        # Process request and get response
        response = self.get_response(request)

        # Log response details
        if request.path.startswith("/oms/"):
            logger.info(f" Response: {response.status_code} {request.path}")
            logger.info(f" Response Body: {response.content.decode('utf-8')}")

        return response
