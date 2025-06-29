"""
Middleware for request logging and monitoring.

This module provides middleware for logging API requests and responses
for monitoring and debugging purposes.
"""

import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for logging API requests and responses.

    This middleware logs detailed information about each API request
    including method, path, user, response time, and status code.
    """

    def process_request(self, request):
        """Log incoming request details."""
        # Store start time for calculating response time
        request.start_time = time.time()

        # Log request details
        user_info = f"User: {request.user.email}" if request.user.is_authenticated else "Anonymous"

        logger.info(
            f"Request: {request.method} {request.path} - {user_info} - "
            f"IP: {self.get_client_ip(request)}"
        )

        # Log request body for non-GET requests (excluding sensitive data)
        if request.method != 'GET' and request.content_type == 'application/json':
            try:
                body = json.loads(request.body.decode('utf-8'))
                # Remove sensitive fields from logging
                sanitized_body = self.sanitize_request_body(body)
                logger.debug(f"Request Body: {sanitized_body}")
            except (json.JSONDecodeError, UnicodeDecodeError):
                logger.debug("Request Body: Unable to parse JSON")

    def process_response(self, request, response):
        """Log response details and calculate response time."""
        if hasattr(request, 'start_time'):
            response_time = time.time() - request.start_time

            user_info = f"User: {request.user.email}" if request.user.is_authenticated else "Anonymous"

            # Log response details
            logger.info(
                f"Response: {request.method} {request.path} - {response.status_code} - "
                f"{user_info} - Time: {response_time:.3f}s"
            )

            # Add response time header
            response['X-Response-Time'] = f"{response_time:.3f}s"

        return response

    def process_exception(self, request, exception):
        """Log exceptions that occur during request processing."""
        user_info = f"User: {request.user.email}" if request.user.is_authenticated else "Anonymous"

        logger.error(
            f"Exception: {request.method} {request.path} - {user_info} - "
            f"Error: {str(exception)}"
        )

    def get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def sanitize_request_body(self, body):
        """Remove sensitive information from request body for logging."""
        if isinstance(body, dict):
            sanitized = body.copy()
            sensitive_fields = ['password', 'password_confirm', 'current_password', 'new_password']

            for field in sensitive_fields:
                if field in sanitized:
                    sanitized[field] = '***REDACTED***'

            return sanitized
        return body


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware for monitoring API performance.

    This middleware tracks slow requests and provides performance metrics.
    """

    SLOW_REQUEST_THRESHOLD = 1.0  # seconds

    def process_request(self, request):
        """Store request start time."""
        request.start_time = time.time()

    def process_response(self, request, response):
        """Monitor response time and log slow requests."""
        if hasattr(request, 'start_time'):
            response_time = time.time() - request.start_time

            # Log slow requests
            if response_time > self.SLOW_REQUEST_THRESHOLD:
                user_info = f"User: {request.user.email}" if request.user.is_authenticated else "Anonymous"

                logger.warning(
                    f"Slow Request: {request.method} {request.path} - "
                    f"{user_info} - Time: {response_time:.3f}s"
                )

            # Add performance headers
            response['X-Response-Time'] = f"{response_time:.3f}s"
            response['X-Slow-Request'] = str(response_time > self.SLOW_REQUEST_THRESHOLD).lower()

        return response