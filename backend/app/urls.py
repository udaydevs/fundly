"Urls for general things are defined here"
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import LineItemViewSet, MatchViewSet, OrganizationView, TransactionView
router = DefaultRouter()
router.register(r'transactions', TransactionView, basename='transaction')
router.register(r'line-items', LineItemViewSet, basename='line-item')
router.register(r'matches', MatchViewSet, basename='match')

urlpatterns = [
    path('org/', OrganizationView.as_view()),
    path('', include(router.urls)),
]