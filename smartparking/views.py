from .models import Reservation, Parking
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from .models import Client, Parking
from django.db.models import Sum, Count, Q, F, ExpressionWrapper, FloatField, Case, When, Value
from django.db.models.functions import Greatest, Extract
from django.views.decorators.csrf import ensure_csrf_cookie
import os
import logging
import json
import locale
from django.db.models import F
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from .models import Client, Reservation, Matricule
from django.db.models import Sum, Count
from django.db.models import Q
from .models import Client
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from .models import Gerant, Parking
from django.contrib import messages
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model, update_session_auth_hash
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Region, Parking, Client, Reservation, Gerant, CustomUser
from django.http import HttpResponseForbidden, JsonResponse
from .utils import generate_password, format_date
from .emails import email_for_new_user, email_confirm_reservation
from .forms import CustomLoginForm, ReservationForm
from django.contrib.auth import logout, login, authenticate
from django.utils import translation

# Paramètres de configuration d'encodage des textes en Français
try:
    locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
except locale.Error:
    # Si le locale français n'est pas disponible, utilisez le locale par défaut
    locale.setlocale(locale.LC_ALL, '')

# Configuration de l'environnement pour Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'votre_projet.settings')

# Activation de la langue française pour Django
translation.activate('fr')

User = get_user_model()

logger = logging.getLogger(__name__)


def home_view(request):
    regions = Region.objects.all()
    parking_actifs = Parking.objects.filter(actif=True)
    parkings = parking_actifs.annotate(
        place_dispo=F('nombre_place') - Reservation.objects.filter(parking=F('id'), status='active').count()).filter(
        place_dispo__gt=0)
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
    if parking.nombre_place_dispo() <= 0:
        messages.warning(request, "Le parking sélectionné n'a plus de place disponible pour une réservation..!")
        return redirect("home")

    parking_nom = parking.nom
    region_nom = parking.region.nom

    request.session['parking_id'] = parking.id

    user_matricules = []
    is_client = False

    if request.user.is_authenticated and hasattr(request.user, 'client_profile'):
        # L'utilisateur est connecté et est un client
        user_matricules = Matricule.objects.filter(client=request.user)
        is_client = True

    if request.method == 'POST':
        return _extracted_from_reservation_view_(request, parking)
    context = {
        'parking': parking,
        'parking_nom': parking_nom,
        'region_nom': region_nom,
        'user_matricules': user_matricules,
        'is_client': is_client,
    }
    return render(request, 'smartparking/reservation.html', context=context)


# TODO Rename this here and in `reservation_view`
def _extracted_from_reservation_view_(request, parking):
    date_arrive = request.POST.get('date_arrive')
    date_sortie = request.POST.get('date_sortie')
    matricule = request.POST.get("matricule_serie") + request.POST.get("matricule_numero")

    # Convertir les dates pour la comparaison

    date_arrive_dt = timezone.make_aware(datetime.strptime(date_arrive, '%Y-%m-%d'))
    date_sortie_dt = timezone.make_aware(datetime.strptime(date_sortie, '%Y-%m-%d'))

    if reservation_existante := Reservation.objects.filter(
            parking=parking,
            date_arrive=date_arrive_dt,
            date_sortie=date_sortie_dt,
            matricule=matricule,
    ).exists():
        messages.warning(request, "Une réservation avec les mêmes dates et matricule existe déjà pour ce parking.")
        return redirect("home")

    request.session['date_arrive'] = date_arrive
    request.session['date_sortie'] = date_sortie
    request.session['matricule'] = matricule

    return redirect('paiement')


def paiement_view(request):
    parking_id = request.session.get('parking_id')
    date_arrive = request.session.get('date_arrive')
    date_sortie = request.session.get('date_sortie')
    price = request.session.get('price')
    matricule = request.session.get('matricule')

    if not all([parking_id, date_arrive, date_sortie, price, matricule]):
        return redirect('home')

    parking = get_object_or_404(Parking, pk=parking_id)
    date_arrive = timezone.make_aware(
        datetime.strptime(date_arrive, '%Y-%m-%d'))
    date_sortie = timezone.make_aware(
        datetime.strptime(date_sortie, '%Y-%m-%d'))

    region_name = parking.region.nom
    parking_name = parking.nom
    date_arrive_str, date_sortie_str = format_date(
        da=date_arrive, ds=date_sortie)

    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            return render(request, 'smartparking/paiement.html', {'error': 'Email is required'})

        User = get_user_model()
        user, created = User.objects.get_or_create(
            email=email, defaults={'user_type': 'client'})

        if created:
            password = generate_password()
            print(password)
            user.set_password(password)
            user.save()
            email_for_new_user(
                request, user, password, path_template='smartparking/emails/send_email_to_new_user.html')
        else:
            user.is_new_user = False
            user.save()

        Client.objects.get_or_create(user=user)
        Matricule.objects.get_or_create(matricule=matricule, client=user)

        reservation = Reservation.objects.create(
            parking=parking,
            client=user,
            date_arrive=date_arrive,
            date_sortie=date_sortie,
            access_code=Reservation().generate_access_code(),
            matricule=matricule
        )
        print(reservation.parking.id, reservation.matricule, reservation.access_code)

        email_confirm_reservation(request, user, reservation)
        for key in ['parking_id', 'date_arrive', 'date_sortie', 'price', 'matricule']:
            request.session.pop(key, None)

        return redirect('confirm_reservation', reservation_id=reservation.id)

    context = {
        'region_name': region_name,
        'parking_name': parking_name,
        'date_arrive': date_arrive_str,
        'date_sortie': date_sortie_str,
        'prix': price,
        'matricule': matricule
    }

    return render(request, 'smartparking/paiement.html', context=context)


def reservation_confirmation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    is_new_user = reservation.client.is_new_user

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

        duration = (date_sortie - date_arrive).days + 1

        if duration <= 0:
            duration = 1

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
    user_logged = request.user

    total_region = Region.objects.count()

    if user_logged.user_type == 'admin':
        parkings = Parking.objects.all()
        clients = CustomUser.objects.filter(user_type='client')
        reservations = Reservation.objects.all()
    elif user_logged.user_type == 'gerant':
        parkings = Parking.objects.filter(gerant__user=user_logged)
        clients = CustomUser.objects.filter(
            reservations__parking__gerant__user=user_logged,
            user_type='client'
        ).distinct()
        reservations = Reservation.objects.filter(
            parking__gerant__user=user_logged).exclude(client=user_logged)
    else:  # client
        parkings = Parking.objects.all()
        clients = CustomUser.objects.none()
        reservations = Reservation.objects.filter(client=user_logged)

    # Calcul du prix personnalisé
    price_calculation = Case(
        When(
            client__user_type='gerant',
            parking__gerant__user=F('client'),
            then=Value(0, output_field=FloatField())
        ),
        default=ExpressionWrapper(
            F('parking__tarif') * Greatest(
                1,
                Extract(
                    F('date_sortie') - F('date_arrive') + timedelta(days=1),
                    'day'
                )
            ),
            output_field=FloatField()
        ),
        output_field=FloatField()
    )

    # Utilisez price_calculation dans votre agrégation
    reservations_stats = reservations.aggregate(
        total_reservation=Count('id'),
        total_reservation_active=Count('id', filter=Q(status='active')),
        total_revenu=Sum(price_calculation)
    )

    # Calcul des parkings populaires
    parkings_with_occupation = parkings.annotate(
        reserved_places=Count('reservations', filter=Q(
            reservations__status='active'))
    )

    parking_populaires = [
        parking for parking in parkings_with_occupation
        if (parking.reserved_places / parking.nombre_place * 100) > 2
    ]

    context = {
        'total_gerant': Gerant.objects.count(),
        'total_client': clients.count(),
        'total_reservation': reservations_stats['total_reservation'] or 0,
        'total_reservation_active': reservations_stats['total_reservation_active'] or 0,
        'total_revenu': reservations_stats['total_revenu'] or 0,
        'parking_populaires': parking_populaires,
        'recervation_recentes': reservations.order_by('-date_arrive')[:3],
        'total_parking': parkings.count(),
        'total_region': total_region
    }

    return render(request, 'smartparking/dashboard.html', context=context)


def gestion_gerant(request):
    return render(request, 'smartparking/gestion_gerant.html')


def get_gerants_data(request):
    gerants = Gerant.objects.all()

    gerants_data = [
        {
            'id': gerant.id,
            'email': gerant.user.email,
            'date_embauche': gerant.user.date_joined.strftime('%d-%m-%Y'),
        }
        for gerant in gerants
    ]
    gerants_data = sorted(gerants_data, key=lambda x: x['id'], reverse=True)

    return JsonResponse({'gerants': gerants_data})


@require_http_methods(["POST"])
def add_gerant(request):
    data = json.loads(request.body)
    try:
        user, created = User.objects.get_or_create(
            email=data['email'],
            defaults={
                'user_type': 'gerant',
            }
        )
        if created:
            password = generate_password()
            user.set_password(password)
            user.save()
            email_for_new_user(
                request, user, password, path_template='smartparking/emails/gerant_email.html')
        else:
            raise ValueError(
                "Un utilisateur avec cette adresse email existe déjà")

        gerant = Gerant.objects.create(
            user=user,
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Gérant ajouté avec succès.',
            'gerant': {
                'id': gerant.id,
                'email': user.email,
                'date_embauche': user.date_joined.strftime('%d-%m-%Y')
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

        gerant.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Gérant mis à jour avec succès.',
            'gerant': {
                'id': gerant.id,
                'email': user.email,
                'date_embauche': user.date_joined.strftime('%d-%m-%Y')
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


def get_gerant(request, gerant_id):
    gerant = get_object_or_404(Gerant, id=gerant_id)
    return JsonResponse({
        'id': gerant.id,
        'email': gerant.user.email,
        'date_embauche': gerant.user.date_joined.strftime('%Y-%m-%d')
    })


def gestion_clients(request):
    return render(request, 'smartparking/gestion_client.html')


def search_clients(request):
    user_logged = request.user
    query = request.GET.get('query', '')

    if user_logged.user_type == 'admin':
        clients = CustomUser.objects.filter(user_type='client').filter(
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).annotate(
            reservations_count=Count(
                'reservations'
            )
        ).order_by('-date_joined')

    elif user_logged.user_type == 'gerant':
        parkings_geres = Parking.objects.filter(gerant__user=user_logged)
        client_ids = Reservation.objects.filter(
            parking__in=parkings_geres
        ).exclude(
            client=user_logged
        ).values_list(
            'client_id', flat=True
        ).distinct()

        clients = CustomUser.objects.filter(id__in=client_ids).filter(
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).annotate(
            reservations_count=Count(
                'reservations',
                filter=Q(reservations__parking__in=parkings_geres)
            )
        )
    else:
        clients = CustomUser.objects.none()

    paginator = Paginator(clients, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    client_data = [{
        'id': client.id,
        'first_name': client.first_name or 'Non defini',
        'last_name': client.last_name or 'Non defini',
        'telephone': client.telephone,
        'email': client.email,
        'date_inscription': client.date_joined.strftime('%d/%m/%Y'),
        'reservations_count': client.reservations_count
    } for client in page_obj]

    return JsonResponse({
        'clients': client_data,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'num_pages': paginator.num_pages,
        'current_page': page_obj.number
    })


@login_required
def client_detail(request, client_id):
    client = get_object_or_404(CustomUser, id=client_id)
    print(client.first_name)

    if request.user.user_type != 'gerant':
        # Handle other user types or raise a permission error
        return HttpResponseForbidden("You don't have permission to view this page.")

    parkings = Parking.objects.filter(gerant__user=request.user)
    reservations = Reservation.objects.filter(
        client=client,
        parking__in=parkings
    ).order_by('-date_arrive')

    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    stats = {
        'reservations_this_month': reservations.filter(date_arrive__gte=month_start).count(),
        'total_amount_spent': reservations.aggregate(total=Sum('parking__tarif'))['total'] or 0,
        'favorite_parking': reservations.values('parking__nom').annotate(count=Count('parking')).order_by(
            '-count').first(),
    }

    active_reservations = reservations.filter(status='active')

    last_12_months = [now - timedelta(days=30 * i) for i in range(12)]
    months_labels = [month.strftime('%b')
                     for month in reversed(last_12_months)]
    years_labels = [month.strftime('%Y') for month in reversed(last_12_months)]

    reservations_count_by_month = []
    for month in reversed(last_12_months):
        month_start = month.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)
                     ).replace(day=1) - timedelta(seconds=1)
        count = reservations.filter(
            date_arrive__gte=month_start, date_arrive__lte=month_end).count()
        reservations_count_by_month.append(count)

    parking_stats = []
    for parking in parkings:
        parking_reservations = reservations.filter(parking=parking)
        parking_stats.append({
            'parking_name': parking.nom,
            'reservation_count': parking_reservations.count(),
            'total_revenue': parking_reservations.aggregate(total=Sum('parking__tarif'))['total'] or 0,
        })

    context = {
        'client': client,
        'reservations': reservations,
        'active_reservations': active_reservations,
        'stats': stats,
        'months_labels': json.dumps(months_labels),
        'years_labels': json.dumps(years_labels),
        'reservations_count_by_month': json.dumps(reservations_count_by_month),
        'parking_stats': parking_stats,
    }

    return render(request, 'smartparking/detail_client.html', context)


def block_client(request, client_id):
    if request.method == 'POST':
        try:
            client = Client.objects.get(id=client_id)
            client.user.is_active = False
            client.user.save()
            return JsonResponse({'success': True})
        except Client.DoesNotExist:
            return JsonResponse({'error': 'Client not found'}, status=404)
    return JsonResponse({'error': 'Invalid request'}, status=400)


def get_reservations(request):
    user_logged = request.user

    # Filtrer les réservations en fonction du type d'utilisateur
    if user_logged.user_type == 'gerant':
        reservations = Reservation.objects.filter(
            parking__gerant__user=user_logged
        ).exclude(client=user_logged)
    elif user_logged.user_type == 'client':
        reservations = Reservation.objects.filter(client=user_logged)
    else:  # Pour les admins ou autres types d'utilisateurs
        reservations = Reservation.objects.all()

    # Mise à jour automatique du statut des réservations
    for reservation in reservations:
        if reservation.status != 'cancel':  # Ne pas modifier les réservations annulées
            if reservation.date_sortie < timezone.now() + timedelta(hours=24):
                reservation.status = 'expired'
            elif reservation.date_arrive <= timezone.now() <= reservation.date_sortie:
                reservation.status = 'active'
            reservation.save()

    # Appliquer les filtres
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    statut = request.GET.get('statut')
    parking_nom = request.GET.get('parking')

    if date_debut:
        reservations = reservations.filter(date_arrive__gte=date_debut)
    if date_fin:
        reservations = reservations.filter(date_sortie__lte=date_fin)
    if statut:
        reservations = reservations.filter(status=statut)
    if parking_nom:
        reservations = reservations.filter(parking__nom=parking_nom)

    # Tri final
    reservations = reservations.order_by("-date_arrive", "-id")

    # Pagination
    paginator = Paginator(reservations, 10)  # 10 réservations par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'reservations': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'paginator': paginator,
        'parkings': Parking.objects.all(),
    }

    return render(request, 'smartparking/gestion_reservations.html', context)


def get_reservation_details(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    data = {
        'client': reservation.client.email,
        'parking': reservation.parking.nom,
        'date_arrive': reservation.date_arrive.strftime('%d-%m-%Y'),
        'date_sortie': reservation.date_sortie.strftime('%d-%m-%Y'),
        'statut': reservation.status,
        'access_code': reservation.access_code,
        'matricule': reservation.matricule,
        'prix': str(reservation.calculate_price)
    }
    return JsonResponse(data)


def update_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    if reservation.status == 'expired':
        return JsonResponse({'success': False, 'message': 'Impossible de modifier une réservation expirée'}, status=400)

    if request.method == 'POST':
        form = ReservationForm(request.POST, instance=reservation)
        if not form.is_valid():
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
        updated_reservation = form.save()
        return JsonResponse({
            'success': True,
            'reservation': {
                'id': updated_reservation.id,
                'client': str(updated_reservation.client),
                'parking': str(updated_reservation.parking.nom),
                'date_arrive': updated_reservation.date_arrive.strftime('%Y-%m-%d'),
                'date_sortie': updated_reservation.date_sortie.strftime('%Y-%m-%d'),
                'statut': updated_reservation.status,
                'access_code': updated_reservation.access_code,
            }
        })
    else:
        form = ReservationForm(instance=reservation)
        return JsonResponse({
            'success': True,
            'form_data': {
                'region': reservation.parking.region.id,
                'parking': reservation.parking.id,
                'date_arrive': reservation.date_arrive.strftime('%Y-%m-%d'),
                'date_sortie': reservation.date_sortie.strftime('%Y-%m-%d'),
                'matricule': reservation.matricule,
                'price': reservation.calculate_price
            },
            'regions': [{'id': region.id, 'nom': region.nom} for region in Region.objects.all()],
            'parkings': [{'id': parking.id, 'nom': parking.nom, 'region_id': parking.region.id} for parking in
                         Parking.objects.all()]
        })


def get_parkings(request, region_id):
    parkings = Parking.objects.filter(region_id=region_id)
    return JsonResponse({
        'parkings': [{'id': parking.id, 'nom': parking.nom} for parking in parkings]
    })


def delete_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    if request.method == 'POST':
        reservation.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


# SECTION GESTION DES REGIONS

def region_list(request):
    return render(request, 'smartparking/gouvernaurat.html')


@require_http_methods(["GET"])
def get_regions(request):
    regions = Region.objects.all()
    data = [{"id": region.id, "nom": region.nom,
             "nombre_parkings": region.parkings.count()} for region in regions]

    data = sorted(data, key=lambda x: x['id'], reverse=True)
    return JsonResponse({"regions": data})


@csrf_exempt
@require_http_methods(["POST"])
def add_region(request):
    try:
        data = json.loads(request.body)
        nom = data.get('nom')
        if not nom:
            return JsonResponse({"message": "Le nom de la région est obligatoire."}, status=400)

        region = Region.objects.create(nom=nom)
        return JsonResponse({"id": region.id, "nom": region.nom, "message": "Région ajoutée avec succès."}, status=201)
    except Exception as e:
        return JsonResponse({"message": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PUT"])
def update_region(request, region_id):
    try:
        region = get_object_or_404(Region, id=region_id)
        data = json.loads(request.body)
        nom = data.get('nom')
        if not nom:
            return JsonResponse({"message": "Le nom de la région est obligatoire."}, status=400)

        region.nom = nom
        region.save()
        return JsonResponse({"id": region.id, "nom": region.nom, "message": "Région mise à jour avec succès."})
    except Exception as e:
        return JsonResponse({"message": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_region(request, region_id):
    try:
        region = get_object_or_404(Region, id=region_id)
        region.delete()
        return JsonResponse({"message": "Région supprimée avec succès."})
    except Exception as e:
        return JsonResponse({"message": str(e)}, status=400)


@require_http_methods(["GET"])
def get_region(request, region_id):
    try:
        region = get_object_or_404(Region, id=region_id)
        return JsonResponse({"id": region.id, "nom": region.nom})
    except Exception as e:
        return JsonResponse({"message": str(e)}, status=400)


# SECTION GESTION PARKING
@login_required
def get_list_parkings(request):
    user_logged = request.user
    if user_logged.user_type in ['admin', 'client']:
        parkings = Parking.objects.all()
    elif user_logged.user_type == 'gerant':
        parkings = Parking.objects.filter(gerant__user=user_logged)

    else:
        parkings = Parking.objects.none()

    regions = Region.objects.all()
    return render(request, 'smartparking/gestion_parking.html', {'parkings': parkings, 'regions': regions})


@login_required
@require_POST
def add_parking(request):
    if request.method != 'POST':
        return
    nom = request.POST.get('nom')
    region_id = request.POST.get('region')
    nombre_place = request.POST.get('nombre_place')
    tarif = request.POST.get('tarif')
    actif = request.POST.get('actif') == 'on'

    if not all([nom, region_id, nombre_place, tarif]):
        return JsonResponse({'success': False, 'error': 'Tous les champs sont obligatoires.'})

    try:
        region = Region.objects.get(id=region_id)
        gerant = Gerant.objects.get(user=request.user)

        parking = Parking.objects.create(
            gerant=gerant,
            nom=nom,
            region=region,
            nombre_place=int(nombre_place),
            tarif=float(tarif),
            actif=actif
        )

        return JsonResponse({
            'success': True,
            'id': parking.id,
            'nom': parking.nom,
            'region': parking.region.nom,
            'nombre_place': parking.nombre_place,
            'nombre_place_dispo': parking.nombre_place_dispo(),
            'tarif': float(parking.tarif),
            'taux_occupation': parking.taux_occupation,
            'actif': parking.actif
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def edit_parking(request):
    if request.method != 'POST':
        return
    parking_id = request.POST.get('parking_id')
    nom = request.POST.get('nom')
    region_id = request.POST.get('region')
    nombre_place = request.POST.get('nombre_place')
    tarif = request.POST.get('tarif')
    actif = request.POST.get('actif') == 'on'

    if not all([parking_id, nom, region_id, nombre_place, tarif]):
        return JsonResponse({'success': False, 'error': 'Tous les champs sont obligatoires.'})

    try:
        parking = get_object_or_404(Parking, id=parking_id)
        region = Region.objects.get(id=region_id)

        parking.nom = nom
        parking.region = region
        parking.nombre_place = int(nombre_place)
        parking.tarif = float(tarif)
        parking.actif = actif
        parking.save()

        return JsonResponse(
            {
                'success': True,
                'id': parking.id,
                'nom': parking.nom,
                'region': parking.region.nom,
                'nombre_place': parking.nombre_place,
                'nombre_place_dispo': parking.nombre_place_dispo(),
                'tarif': parking.tarif,
                'taux_occupation': parking.taux_occupation,
                'actif': parking.actif,
            }
        )
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_parking_details(request, parking_id):
    parking = get_object_or_404(Parking, id=parking_id)
    return JsonResponse({
        'id': parking.id,
        'nom': parking.nom,
        'region': parking.region.id,
        'nombre_place': parking.nombre_place,
        'nombre_place_dispo': parking.nombre_place_dispo(),
        'tarif': float(parking.tarif),
        'taux_occupation': parking.taux_occupation,
        'actif': parking.actif
    })


@login_required
@require_POST
def delete_parking(request):
    if request.method == 'POST':
        parking_id = request.POST.get('parking_id')
        try:
            parking = get_object_or_404(Parking, id=parking_id)
            parking_name = parking.nom  # Sauvegardez le nom avant la suppression
            parking.delete()
            return JsonResponse(
                {'success': True, 'message': f'Le parking "{parking_name}" a été supprimé avec succès.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@login_required
def search_parkings(request):
    user_logged = request.user
    query = request.GET.get('q', '')
    if user_logged.user_type == 'admin':
        parkings = Parking.objects.filter(
            Q(nom__icontains=query) |
            Q(region__nom__icontains=query)
        )
    elif user_logged.user_type == 'gerant':
        parkings = Parking.objects.filter(gerant__user=user_logged)
        parkings = parkings.filter(
            Q(nom__icontains=query) |
            Q(region__nom__icontains=query)
        )
    else:
        parkings = Parking.objects.none()

    return JsonResponse({
        'parkings': [
            {
                'id': p.id,
                'nom': p.nom,
                'region': p.region.nom,
                'nombre_place': p.nombre_place,
                'nombre_place_dispo': p.nombre_place_dispo(),
                'tarif': float(p.tarif),
                'taux_occupation': p.taux_occupation,
                'actif': p.actif
            } for p in parkings
        ]
    })


# Dashboard Client

@login_required
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def make_reservation(request):
    user_logged = request.user
    if request.method == "GET":
        if user_logged.user_type == 'client':
            parkings = Parking.objects.filter(actif=True)
            matricules = Matricule.objects.filter(client=user_logged)

        elif user_logged.user_type == 'gerant':
            parkings = Parking.objects.filter(actif=True, gerant__user=user_logged)
            matricules = []

        context = {
            'parkings': parkings,
            'matricules': matricules
        }
        return render(request, 'smartparking/faire_reservation.html', context)

    elif request.method == "POST":
        parking_id = request.POST.get('parking_id')
        matricule = request.POST.get('matricule_serie') + request.POST.get('matricule_numero')
        date_arrive = request.POST.get('date_arrive')
        date_sortie = request.POST.get('date_sortie')

        parking = Parking.objects.get(id=parking_id)
        if parking.nombre_place_dispo() <= 0:
            return JsonResponse({'status': 'error', 'message': 'Pas de place disponible'})

        reservation = Reservation.objects.create(
            parking=parking,
            client=request.user,
            date_arrive=datetime.strptime(date_arrive, '%Y-%m-%d'),
            date_sortie=datetime.strptime(date_sortie, '%Y-%m-%d'),
            matricule=matricule,
            access_code=Reservation().generate_access_code()
        )

        Matricule.objects.get_or_create(matricule=matricule, client=request.user)

        return JsonResponse({
            'status': 'success',
            'message': 'Réservation effectuée',
            'access_code': reservation.access_code,
            'total_price': reservation.calculate_price
        })


@login_required
def get_matricules(request):
    matricules = Matricule.objects.filter(
        client=request.user).values_list('matricule', flat=True)
    return JsonResponse(list(matricules), safe=False)


# SECTION PARAMETRE
def setup_parameter(request):
    return render(request, 'smartparking/parametre.html')


@login_required
@require_POST
def update_user_info(request):
    user = request.user
    user.first_name = request.POST.get('first_name')
    user.last_name = request.POST.get('last_name')
    user.telephone = request.POST.get('telephone')
    user.save()
    return JsonResponse({'status': 'success'})


@login_required
@require_POST
def change_password(request):
    user = request.user
    current_password = request.POST.get('current_password')
    new_password = request.POST.get('new_password')

    if user.check_password(current_password):
        user.set_password(new_password)
        user.save()
        # Important pour maintenir la session de l'utilisateur
        update_session_auth_hash(request, user)
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error'}, status=400)


# Vues supplementaires
@require_http_methods(["GET"])
def get_parking_price(request, parking_id):
    parking = get_object_or_404(Parking, id=parking_id)
    return JsonResponse({"tarif": float(parking.tarif)})


@require_GET
def check_user_type(request):
    if request.user.is_authenticated:
        return JsonResponse({'user_type': request.user.user_type})
    return JsonResponse({'user_type': 'anonymous'}, status=401)


def is_gerant(user):
    return user.user_type == 'gerant'


@login_required
@user_passes_test(is_gerant)
def gerant_reservations(request):
    gerant = request.user.gerant_profile
    parkings = Parking.objects.filter(gerant=gerant)
    reservations = Reservation.objects.filter(client=request.user,
                                              parking__in=parkings).order_by('-date_arrive')

    # Apply filters
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    statut = request.GET.get('statut')

    if date_debut:
        reservations = reservations.filter(date_arrive__gte=date_debut)
    if date_fin:
        reservations = reservations.filter(date_sortie__lte=date_fin)
    if statut:
        reservations = reservations.filter(status=statut)

    # Pagination
    paginator = Paginator(reservations, 10)  # 10 reservations per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'reservations': page_obj,
        'parkings': parkings,
    }
    return render(request, 'smartparking/gerant_reservations.html', context)


# @csrf_exempt
# @require_POST
# def verify_access(request):
#     matricule = request.POST.get('matricule')
#     parking_id = request.POST.get('parking_id')
#     access_type = request.POST.get('type')

#     if not all([matricule, parking_id, access_type]):
#         return JsonResponse({'action': 'deny', 'led': 'red'}, status=400)

#     parking = Parking.objects.get(id=parking_id)
#     now = timezone.now()

#     reservation = Reservation.objects.filter(
#         parking=parking,
#         matricule=matricule,
#         date_debut__lte=now,
#         date_fin__gte=now,
#         status='active'
#     ).first()

#     if not reservation:
#         return JsonResponse({'action': 'deny', 'led': 'red'})

#     if access_type == 'entree':
#         # Vérifier si le véhicule est déjà dans le parking
#         derniere_entree_sortie = EntreSortie.objects.filter(
#             reservation=reservation).last()
#         if derniere_entree_sortie and derniere_entree_sortie.heure_sortie is None:
#             return JsonResponse({'action': 'deny', 'led': 'red', 'message': 'Véhicule déjà dans le parking'})

#         # Créer une nouvelle entrée
#         EntreSortie.objects.create(reservation=reservation, heure_entree=now)
#         return JsonResponse({
#             'action': 'open',
#             'led': 'green',
#             'access_code': reservation.access_code
#         })

#     elif access_type == 'sortie':
#         if derniere_entree := EntreSortie.objects.filter(
#             reservation=reservation, heure_sortie__isnull=True
#         ).last():
#             derniere_entree.heure_sortie = now
#             derniere_entree.save()

#             # Vérifier si c'est la dernière sortie de la réservation
#             if now >= reservation.date_fin:
#                 reservation.status = 'completed'
#                 reservation.save()

#             return JsonResponse({'action': 'open', 'led': 'green'})
#         else:
#             return JsonResponse({'action': 'deny', 'led': 'red', 'message': 'Aucune entrée correspondante trouvée'})

#     else:
#         return JsonResponse({'action': 'deny', 'led': 'red'}, status=400)

@csrf_exempt
def verify_access(request):
    if request.method not in ['GET', 'POST']:
        return JsonResponse({'action': 'refusé', 'led': 'rouge'}, status=405)

    matricule = request.GET.get('matricule')
    parking_id = request.GET.get('parking_id')
    access_type = request.GET.get('type')
    code_access = request.GET.get('code_acces')


 
    if not all([matricule, parking_id, access_type]):
        return JsonResponse({'action': 'refusé', 'led': 'rouge'}, status=400)

    try:
        parking = Parking.objects.get(id=parking_id)

    except Parking.DoesNotExist:
        return JsonResponse({'action': 'refusé', 'led': 'rouge'}, status=404)

    now = timezone.now()

    reservation = Reservation.objects.filter(
        parking=parking,
        matricule=matricule,
        date_arrive__lte=now,
        date_sortie__gte=now,
        status='active'
    ).first()

    print(reservation)

    if not reservation:
        print({'message': 'Aucune reservation trouvée'})

    if access_type == 'entree':
        reservation.status = 'expired'
        reservation.save()

        return JsonResponse({
            'action': 'ouvert',
            'led': 'vert',
            'access_code': reservation.access_code,
            'message': 'Vehicule entre dans le parking'
        })

    elif access_type == 'sortie':
        nombre_place = parking.nombre_place_dispo()
        nombre_place += 1
        
        return JsonResponse({'message': 'fait'})
      
    else:
        return JsonResponse({'action': 'refusé', 'led': 'rouge'}, status=400)
