from django.urls import path

urlpatterns = [
    path("", lambda request: None, name="noop"),
]
