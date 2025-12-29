from django.urls import path
from . import views

urlpatterns = [
    path("api/v1/calculate_quantity/", views.calculate_quantity, name="calculate-quantity"),

    path("api/health/", views.health_check, name="health-check"),
]
