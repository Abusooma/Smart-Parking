from django.conf import settings
import random
import string
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta, timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('client', 'Client'),
        ('gerant', 'Gérant'),
        ('admin', 'Admin'),
    ]

    username = None
    email = models.EmailField(_('email address'), unique=True)
    is_new_user = models.BooleanField(default=True)
    user_type = models.CharField(max_length=50, choices=USER_TYPE_CHOICES)
    telephone = models.CharField(max_length=12, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        return self.email or 'N/A'
    
    @property
    def fullname(self):
        return f"{self.first_name} {self.last_name}"
    

class Region(models.Model):
    nom = models.CharField(max_length=150)

    def __str__(self):
        return self.nom or 'N/A'

class Client(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='client_profile')

    def __str__(self):
        return f"{self.user.email} - Client"
    

class Gerant(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gerant_profile')

    def __str__(self):
        return f"{self.user.email} - Gérant"

class Parking(models.Model):
    gerant = models.ForeignKey(Gerant, on_delete=models.CASCADE, null=True)
    nom = models.CharField(max_length=100)
    nombre_place = models.IntegerField()
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='parkings')
    tarif = models.DecimalField(max_digits=10, decimal_places=2)
    actif = models.BooleanField(default=True)

    def nombre_place_dispo(self):
        place_reservees = Reservation.objects.filter(parking=self, status='active').count()
        return self.nombre_place - place_reservees
    
    @property
    def taux_occupation(self):
        if self.nombre_place == 0:
            return 0
        place_reservees = Reservation.objects.filter(parking=self, status='active').count()
        return (place_reservees / self.nombre_place) * 100

    def __str__(self):
        return f"{self.nom} ({self.region})"


class Reservation(models.Model):
    STATUS = [
        ('active', 'active'), 
        ('expired', 'expirée'),
        ('cancel', 'annulée')
    ]
    parking = models.ForeignKey(Parking, on_delete=models.CASCADE, blank=True, related_name='reservations')
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    date_arrive = models.DateTimeField()
    date_sortie = models.DateTimeField()
    status = models.CharField(max_length=25, choices=STATUS, default='active')
    access_code = models.CharField(max_length=7, blank=True, null=True)
    matricule = models.CharField(max_length=30, null=True, blank=True)

    @property
    def verif_is_expired(self):
        if self.date_sortie < timezone.now() + timedelta(hours=24):
            self.status = 'expired'

    def generate_access_code(self, lenth_digit=4):
        digits = random.choices(string.digits, k=lenth_digit) 
        code = digits
        random.shuffle(code)
        return ''.join(code)

    @property
    def calculate_price(self):
        if self.client and self.client.user_type == 'gerant' and self.parking.gerant and self.parking.gerant.user == self.client:
            return 0
        
        duration = (self.date_sortie - self.date_arrive).days + 1
        if duration <= 0:
            duration = 1 

        return float(self.parking.tarif) * duration 

    def __str__(self):
        return f"Réservation {self.id} pour {self.client} au {self.parking}"


class Matricule(models.Model):
    matricule = models.CharField(max_length=30)
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.matricule
    

