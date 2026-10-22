"Urls for general things are defined here"
from django.urls import path
from .views import OrganizationView
urlpatterns = [
    path('org/', OrganizationView.as_view()),
]