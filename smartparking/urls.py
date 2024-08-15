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
    # Gestion des gerants
    path('dashboard/admin/gestion-gerant', views.gestion_gerant, name='gerants'),
    path('get_gerants_data/', views.get_gerants_data, name='get_gerants_data'),
    path('add-gerant/', views.add_gerant, name='add_gerant'),
    path('update-gerant/<int:gerant_id>/', views.update_gerant, name='update_gerant'),
    path('delete-gerant/<int:gerant_id>/', views.delete_gerant, name='delete_gerant'),
    path('get-parkings/', views.get_parkings, name='get_parkings'),
    path('get-gerant/<int:gerant_id>/', views.get_gerant, name='get_gerant'),
]