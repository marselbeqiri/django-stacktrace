from django.urls import path

from example.views import stacktrace_view

urlpatterns = [
    path("<str:error_type>/", stacktrace_view, name="stacktrace_view"),
]
