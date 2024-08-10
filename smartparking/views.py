from django.shortcuts import render


def home_view(request):
    return render(request, 'smartparking/index.html')

def reservation_view(request, pk):
    return render(request, 'smartparking/reservation.html')


def paiement_view(request):
    return render(request, 'smartparking/paiement.html')
