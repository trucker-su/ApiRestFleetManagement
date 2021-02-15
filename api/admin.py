from django.contrib import admin
from .models import VehicleType, Vehicle, AllowedTypes, User, Reservation, Track, Incident

# Register your models here.
admin.site.register(VehicleType)
admin.site.register(Vehicle)
admin.site.register(User)
admin.site.register(AllowedTypes)
admin.site.register(Incident)
admin.site.register(Reservation)
admin.site.register(Track)