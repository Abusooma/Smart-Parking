from math import ceil
from django.contrib import messages
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Region, Parking, Client, Reservation
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .utils import generate_password, format_date
from .emails import email_for_new_user, email_confirm_reservation
from .forms import CustomLoginForm
from django.contrib.auth import logout, login, authenticate


def home_view(request):
    regions = Region.objects.all()
    parkings = Parking.objects.filter(actif=True)
    context = {
        'regions': regions,
        'parkings': parkings,
    }
    return render(request, 'smartparking/index.html', context=context)


def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Connexion reussie')
                return redirect('dashboard')
            else:
                messages.error(
                    request, "Une erreur s'est produite lors de la connexion.")
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = CustomLoginForm()

    return render(request, 'smartparking/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('home')

def reservation_view(request, *args, **kwargs):
    pk = kwargs.get('pk')
    parking = get_object_or_404(Parking, pk=pk)
    parking_nom = parking.nom
    region_nom = parking.region.nom

    request.session['parking_id'] = parking.id

    if request.method == 'POST':
        date_arrive = request.POST.get('date_arrive')
        date_sortie = request.POST.get('date_sortie')
        request.session['date_arrive'] = date_arrive
        request.session['date_sortie'] = date_sortie
        return redirect('paiement')

    context = {
        'parking': parking,
        'parking_nom': parking_nom,
        'region_nom': region_nom
    }
    return render(request, 'smartparking/reservation.html', context=context)


def paiement_view(request):
    parking_id = request.session.get('parking_id')
    date_arrive = request.session.get('date_arrive')
    date_sortie = request.session.get('date_sortie')
    price = request.session.get('price')

    if not all([parking_id, date_arrive, date_sortie, price]):
        # Rediriger vers une page d'erreur ou la page d'accueil si les données sont manquantes
        return redirect('home')

    parking = get_object_or_404(Parking, pk=parking_id)
    date_arrive = timezone.make_aware(datetime.strptime(date_arrive, '%Y-%m-%d'))
    date_sortie = timezone.make_aware(datetime.strptime(date_sortie, '%Y-%m-%d'))

    region_name = parking.region.nom
    parking_name = parking.nom
    date_arrive_str, date_sortie_str = format_date(da=date_arrive, ds=date_sortie)

    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            # Gérer l'erreur si l'email n'est pas fourni
            return render(request, 'smartparking/paiement.html', {'error': 'Email is required'})

        User = get_user_model()
        user, created = User.objects.get_or_create(
            email=email, defaults={'user_type': 'client'})

        if created:
            password = generate_password()
            user.set_password(password)
            user.save()
            email_for_new_user(request, user, password)
        
        else:
            user.is_new_user = False
            user.save()
            
    
        client_profile, _ = Client.objects.get_or_create(user=user)

        # Création de Reservation
        reservation = Reservation.objects.create(
            parking=parking,
            client=client_profile,
            date_arrive=date_arrive,
            date_sortie=date_sortie
        )

        email_confirm_reservation(request, user, reservation)
        # Nettoyage de la session
        for key in ['parking_id', 'date_arrive', 'date_sortie', 'price']:
            request.session.pop(key, None)

        return redirect('confirm_reservation', reservation_id=reservation.id)

    context = {
        'region_name': region_name,
        'parking_name': parking_name,
        'date_arrive': date_arrive_str,
        'date_sortie': date_sortie_str,
        'prix': price
    }

    return render(request, 'smartparking/paiement.html', context=context)


def reservation_confirmation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    is_new_user = reservation.client.user.is_new_user

    context = {
        'reservation': reservation,
        'is_new_user': is_new_user,
    }

    return render(request, 'smartparking/confirme_reservation.html', context)


def calculate_price(request):
    parking_id = request.GET.get('parking_id')
    date_arrive = request.GET.get('date_arrive')
    date_sortie = request.GET.get('date_sortie')

    if not parking_id:
        return JsonResponse({'error': 'Parking ID is required'}, status=400)

    try:
        parking = get_object_or_404(Parking, id=parking_id)
        date_arrive = datetime.strptime(date_arrive, '%Y-%m-%d')
        date_sortie = datetime.strptime(date_sortie, '%Y-%m-%d')

        duration = (date_sortie - date_arrive).days

        if duration == 0:
            duration +=1

        if (date_sortie - date_arrive).seconds > 0:
            duration += 1

        price = float(parking.tarif) * duration
        request.session['price'] = str(price)

        return JsonResponse({
            'price': price,
            'duration': duration
        })
    except Exception as e:
        return JsonResponse({'error': 'Une erreur est survenue'}, status=500)

@login_required
def dashboard_view(request):
    return render(request, 'smartparking/dashboard.html')