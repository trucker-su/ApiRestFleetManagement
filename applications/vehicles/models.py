import uuid

from django.core.validators import MinLengthValidator
from django.db import models

from applications.traccar.models import Device

# In Spain vehicle's number plates have 6 characters, except for motorbikes
LENGTH_NUMBER_PLATE = 6


class Vehicle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    model = models.CharField(max_length=50)
    # Brand: Marca de coche
    brand = models.CharField(max_length=20)
    # Número de matricula
    number_plate = models.CharField(
        max_length=LENGTH_NUMBER_PLATE,
        validators=[MinLengthValidator(LENGTH_NUMBER_PLATE)],
        unique=True
    )
    gps_device = models.OneToOneField(Device, null=True, on_delete=models.SET_NULL)

    date_stored = models.DateField(auto_now_add=True)
    is_disabled = models.BooleanField(default=False)

    def __str__(self):
        return '{0} {1}'.format(self.brand, self.model)

    class Meta:
        db_table = 'Vehicle'
