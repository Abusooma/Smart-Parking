from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('reservation/<int:pk>/', views.reservation_view, name='reservation'),
    path('paiement/', views.paiement_view, name='paiement'),
    path('calculate-price/', views.calculate_price, name='calculate-price')
]