import contextlib
from .models import Reservation, Region, Parking
from django.contrib.auth import authenticate
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model


class CustomLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Adresse e-mail'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
    )

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if user is None:
                raise forms.ValidationError("Email ou mot de passe incorrect.")

        return self.cleaned_data
    

class ReservationForm(forms.ModelForm):
    region = forms.ModelChoiceField(
        queryset=Region.objects.all(), required=True)
    parking = forms.ModelChoiceField(
        queryset=Parking.objects.all(), required=True)

    class Meta:
        model = Reservation
        fields = ['region', 'parking', 'date_arrive',
                  'date_sortie', 'matricule']
        widgets = {
            'date_arrive': forms.DateInput(attrs={'type': 'date'}),
            'date_sortie': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['region'].initial = self.instance.parking.region
            self.fields['parking'].queryset = Parking.objects.filter(
                region=self.instance.parking.region)
            self.fields['parking'].initial = self.instance.parking
        elif 'region' in self.data:
            with contextlib.suppress(ValueError, TypeError):
                region_id = int(self.data.get('region'))
                self.fields['parking'].queryset = Parking.objects.filter(
                    region_id=region_id)

    def clean(self):
        cleaned_data = super().clean()
        date_arrive = cleaned_data.get('date_arrive')
        date_sortie = cleaned_data.get('date_sortie')

        if date_arrive and date_sortie and date_arrive > date_sortie:
            raise forms.ValidationError(
                "La date d'arrivée ne peut pas être postérieure à la date de sortie.")

        return cleaned_data
    

class ReservationForm(forms.ModelForm):
    region = forms.ModelChoiceField(
        queryset=Region.objects.all(), required=True)
    parking = forms.ModelChoiceField(
        queryset=Parking.objects.all(), required=True)

    class Meta:
        model = Reservation
        fields = ['region', 'parking', 'date_arrive',
                  'date_sortie', 'matricule']
        widgets = {
            'date_arrive': forms.DateInput(attrs={'type': 'date'}),
            'date_sortie': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['region'].initial = self.instance.parking.region

        if 'region' in self.data:
            with contextlib.suppress(ValueError, TypeError):
                region_id = int(self.data.get('region'))
                self.fields['parking'].queryset = Parking.objects.filter(
                    region_id=region_id)
        elif self.instance.pk:
            self.fields['parking'].queryset = Parking.objects.filter(
                region=self.instance.parking.region)

    def clean(self):
        cleaned_data = super().clean()
        region = cleaned_data.get('region')
        parking = cleaned_data.get('parking')
        date_arrive = cleaned_data.get('date_arrive')
        date_sortie = cleaned_data.get('date_sortie')

        if region and parking:
            if parking.region != region:
                self.add_error(
                    'parking', "Le parking sélectionné n'appartient pas à la région choisie.")

        if date_arrive and date_sortie and date_arrive > date_sortie:
            raise forms.ValidationError(
                "La date d'arrivée ne peut pas être postérieure à la date de sortie.")

        return cleaned_data
