from django.urls import path

from . import views

app_name = "rental"

urlpatterns = [
    path("", views.tool_list, name="tool_list"),
    path("tools/new/", views.tool_create, name="tool_create"),
    path("tools/<int:pk>/edit/", views.tool_update, name="tool_update"),
    path("tools/<int:pk>/delete/", views.tool_delete, name="tool_delete"),
    path("availability/", views.availability_check, name="availability"),
    path("calculator/", views.cost_calculator, name="calculator"),
    path("demo-404/", views.demo_404, name="demo_404"),
]