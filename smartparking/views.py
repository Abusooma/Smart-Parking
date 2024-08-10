from django.shortcuts import render
from .models import Region, Parking


def home_view(request):
    regions = Region.objects.all()
    parkings = Parking.objects.filter(actif=True)
    context = {
        'regions': regions,
        'parkings': parkings,
    }
    return render(request, 'smartparking/index.html', context=context)


def reservation_view(request, pk):
    return render(request, 'smartparking/reservation.html')


def paiement_view(request):
    return render(request, 'smartparking/paiement.html')
