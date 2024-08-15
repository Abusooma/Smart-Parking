from django.core import serializers
from django.shortcuts import render, get_object_or_404
import json
from .models import Gerant, Parking
from django.views.decorators.http import require_http_methods
from math import ceil
from django.contrib import messages
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Region, Parking, Client, Reservation, Gerant, Client
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .utils import generate_password, format_date
from .emails import email_for_new_user, email_confirm_reservation
from .forms import CustomLoginForm
from django.contrib.auth import logout, login, authenticate
import locale

User = get_user_model()

locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')

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
    parkings = Parking.objects.all()
    reservations = Reservation.objects.all()
    total_gerant = Gerant.objects.all().count()
    total_reservation = Reservation.objects.all().count()
    total_client = Client.objects.all().count()
    total_revenu = sum(reservation.calculate_price for reservation in reservations)
    parking_populaires = [parking for parking in parkings if parking.taux_occupation >= 10]

    context = {
        'total_gerant': total_gerant,
        'total_client': total_client,
        'total_reservation': total_reservation,
        'total_revenu': total_revenu,
        'parking_populaires': parking_populaires,
        'recervation_recentes': reservations[:4]
    }
    return render(request, 'smartparking/dashboard.html', context=context)


def gestion_gerant(request):
    return render(request, 'smartparking/gestion_gerant.html')


def get_gerants_data(request):
    gerants = Gerant.objects.all().select_related(
        'user').prefetch_related('parkings')

    gerants_data = []
    for gerant in gerants:
        # Formater la date
        date_embauche = gerant.date_embauche.strftime("%d %B %Y")
        # Corriger les caractères spéciaux
        date_embauche = date_embauche.encode('latin1').decode('utf-8')

        gerants_data.append({
            'id': gerant.id,
            'nom': gerant.user.get_full_name(),
            'email': gerant.user.email,
            'parkings': [parking.nom for parking in gerant.parkings.all()],
            'date_embauche': date_embauche,  # Date formatée
        })
        # Trié par ordre decroissant
        gerants_data = sorted(gerants_data, key=lambda x: x['id'], reverse=True)

    return JsonResponse({'gerants': gerants_data})


@require_http_methods(["POST"])
def add_gerant(request):
    data = json.loads(request.body)
    try:
        user, created = User.objects.get_or_create(
            email=data['email'],
            defaults={'user_type': 'gerant'}
        )
        if created:
            password = generate_password()
            user.set_password(password)
            user.save()
        else:
            raise ValueError("Un utilisateur avec cette adresse email existe déjà")

        date_embauche = data['date_embauche']
        date_embauche = timezone.make_aware(datetime.strptime(date_embauche, '%Y-%m-%d'))
        gerant = Gerant.objects.create(
            user=user,
            date_embauche=date_embauche
        )
        parking_ids = data.get('parkings', [])
        gerant.parkings.set(parking_ids)

        return JsonResponse({
            'status': 'success',
            'message': 'Gérant ajouté avec succès.',
            'gerant': {
                'id': gerant.id,
                'name': user.get_full_name(),
                'email': user.email,
                'parkings': list(gerant.parkings.values_list('nom', flat=True)),
                'date_embauche': gerant.date_embauche.strftime('%Y-%m-%d')
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_http_methods(["POST"])
def update_gerant(request, gerant_id):
    gerant = get_object_or_404(Gerant, id=gerant_id)
    data = json.loads(request.body)
    try:
        user = gerant.user
        user.email = data['email']
        user.save()

        date_embauche = data['date_embauche']
        date_embauche = timezone.make_aware(
            datetime.strptime(date_embauche, '%Y-%m-%d'))

        gerant.date_embauche = date_embauche
        gerant.save()

        parking_ids = data.get('parkings', [])
        gerant.parkings.set(parking_ids)

        return JsonResponse({
            'status': 'success',
            'message': 'Gérant mis à jour avec succès.',
            'gerant': {
                'id': gerant.id,
                'name': user.get_full_name(),
                'email': user.email,
                'parkings': list(gerant.parkings.values_list('nom', flat=True)),
                # Format YYYY-MM-DD
                'date_embauche': gerant.date_embauche.strftime('%Y-%m-%d')
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_http_methods(["POST"])
def delete_gerant(request, gerant_id):
    gerant = get_object_or_404(Gerant, id=gerant_id)
    try:
        user = gerant.user
        gerant.delete()
        user.delete()
        return JsonResponse({'status': 'success', 'message': 'Gérant supprimé avec succès.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def get_parkings(request):
    parkings = Parking.objects.filter(actif=True).values('id', 'nom')
    return JsonResponse(list(parkings), safe=False)


def get_gerant(request, gerant_id):
    gerant = get_object_or_404(Gerant, id=gerant_id)
    return JsonResponse({
        'id': gerant.id,
        'email': gerant.user.email,
        'parkings': list(gerant.parkings.values_list('id', flat=True)),
        # Format YYYY-MM-DD
        'date_embauche': gerant.date_embauche.strftime('%Y-%m-%d')
    })
