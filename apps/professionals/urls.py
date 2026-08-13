from django.urls import path

from .views import directory

app_name = "professionals"

urlpatterns = [path("", directory, name="directory")]
