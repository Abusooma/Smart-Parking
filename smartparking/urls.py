from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('reservation/<int:pk>/', views.reservation_view, name='reservation'),
    path('paiement/', views.paiement_view, name='paiement'),
    path('confirmation-reservation/<int:reservation_id>/', views.reservation_confirmation, name='confirm_reservation'),
    path('calculate-price/', views.calculate_price, name='calculate-price'),
    # URLS FOR DASHBOARD
    path('dashboard/admin/', views.dashboard_view, name='dashboard'),
]