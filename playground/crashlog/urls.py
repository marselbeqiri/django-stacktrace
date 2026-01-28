from django.urls import path

from crashlog.views import crashlog_view

urlpatterns = [
    path("crashlog/<str:error_type>/", crashlog_view, name="crashlog_view"),
]
