from django.core import exceptions as django_exceptions
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from requests import exceptions as requests_exceptions
from django.http import JsonResponse

ERRORS_MAPPER = {
    "ValueError": ValueError,
    "KeyError": KeyError,
    "IndexError": IndexError,
    "TypeError": TypeError,
    "ZeroDivisionError": ZeroDivisionError,
    "AttributeError": AttributeError,
    # Requests lib errors
    "RequestException": requests_exceptions.RequestException,
    "HTTPError": requests_exceptions.HTTPError,
    "ConnectionError": requests_exceptions.ConnectionError,
    "Timeout": requests_exceptions.Timeout,
    "TooManyRedirects": requests_exceptions.TooManyRedirects,
    # Django specific errors
    "FieldDoesNotExist": django_exceptions.FieldDoesNotExist,
    "ObjectDoesNotExist": django_exceptions.ObjectDoesNotExist,
    "MultipleObjectsReturned": django_exceptions.MultipleObjectsReturned,
    "SuspiciousOperation": django_exceptions.SuspiciousOperation,
    "PermissionDenied": django_exceptions.PermissionDenied,
    "FieldError": django_exceptions.FieldError,
    "ValidationError": django_exceptions.ValidationError,
}


@csrf_exempt
def crashlog_view(request, error_type):
    exception_class = ERRORS_MAPPER.get(error_type)
    if exception_class:
        raise exception_class(f"This is a simulated {error_type} for testing purposes.")
    else:
        return JsonResponse({"error": "Unknown error type"}, status=400)
