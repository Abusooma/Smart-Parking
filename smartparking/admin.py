from django.contrib import admin
from .models import CustomUser, Region, Parking, Client, Gerant, Reservation


admin.site.register(CustomUser)
admin.site.register(Region)
admin.site.register(Parking)
admin.site.register(Client)
admin.site.register(Gerant)
admin.site.register(Reservation)

