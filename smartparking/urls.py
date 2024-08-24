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
    path('dashboard/admin/gerants', views.gestion_gerant, name='gerants'),
    path('get_gerants_data/', views.get_gerants_data, name='get_gerants_data'),
    path('add-gerant/', views.add_gerant, name='add_gerant'),
    path('update-gerant/<int:gerant_id>/', views.update_gerant, name='update_gerant'),
    path('delete-gerant/<int:gerant_id>/', views.delete_gerant, name='delete_gerant'),
    path('get-parkings/', views.get_parkings, name='get_parkings'),
    path('get-gerant/<int:gerant_id>/', views.get_gerant, name='get_gerant'),
    # Gestion des clients
    path('dashboard/admin/clients', views.gestion_clients, name='clients'),
    path('search-clients/', views.search_clients, name='search_clients'),
    path('get-client-details/<int:client_id>/', views.client_detail, name='client_details'),
    path('block-client/<int:client_id>/', views.block_client, name='block_client'),
    # Gestion des Reservations
    path('reservations/', views.get_reservations, name='reservations'),
    path('reservations/<int:reservation_id>/details/', views.get_reservation_details, name='reservation_details'),
    path('reservations/<int:reservation_id>/update/', views.update_reservation, name='update_reservation'),
    path('reservations/<int:reservation_id>/delete/', views.delete_reservation, name='delete_reservation'),
    # UPDATE RESERVATION
    path('get_parkings/<int:region_id>/', views.get_parkings_by_region, name='get_parkings_by_region'),
    path('get_parking_price/<int:parking_id>/', views.get_parking_price, name='get_parkings_price'),
    # Gestion des Régions
    path('regions/', views.region_list, name='regions'),
    path('get-regions/', views.get_regions, name='get_regions'),
    path('add-region/', views.add_region, name='add_region'),
    path('update-region/<int:region_id>/', views.update_region, name='update_region'),
    path('delete-region/<int:region_id>/', views.delete_region, name='delete_region'),
    path('get-region/<int:region_id>/', views.get_region, name='get_region'),
    # Gestion des Parkings
    path('parkings/', views.get_list_parkings, name='parkings'),
    path('add_parking/', views.add_parking, name='add_parking'),
    path('edit_parking/', views.edit_parking, name='edit_parking'),
    path('get_parking_details/<int:parking_id>/', views.get_parking_details, name='get_parking_details'),
    path('delete_parking/', views.delete_parking, name='delete_parking'),
    path('search_parkings/', views.search_parkings, name='search_parkings'),
    # Dashboard Client
    path('dashboard/user-client/', views.make_reservation, name='reserver'),
    path('dashboard/type/user-client/get-matricules/', views.get_matricules, name='get_matricules'),
    path('check-user-type/', views.check_user_type, name='check_user_type'),

    # Parametre
    path('dashboard/parametre/', views.setup_parameter, name='parametres'),
]