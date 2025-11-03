# audit_trail/request.py
from threading import local

_thread_locals = local()

def set_current_request(request):
    """Saves the request object in thread-local storage."""
    _thread_locals.request = request

def get_current_request():
    """Returns the request object from thread-local storage."""
    return getattr(_thread_locals, 'request', None)

class AuditMiddleware:
    """Middleware to capture the request for the audit trail."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_request(request)
        response = self.get_response(request)
        set_current_request(None)
        return response