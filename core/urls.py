from django.urls import path
from . import views
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("medications/", views.medication_list, name="medication_list"),
    path("medications/add/", views.medication_create, name="medication_add"),
    path("medications/<int:pk>/edit/", views.medication_edit, name="medication_edit"),
    path("medications/<int:pk>/delete/", views.medication_delete, name="medication_delete"),
    path("notifications/", views.notifications, name="notifications"),
    path("finder/", views.location_finder, name="location_finder"),
]
