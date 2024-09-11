# SmartParking

![Logo SmartParking](https://github.com/Abusooma/Smart-Parking/blob/main/.github/cap1.png)

SmartParking est une plateforme innovante de réservation de parkings développée avec Django. Elle offre aux clients la possibilité de réserver facilement des places de stationnement en fonction de leur localisation.

## Aperçu

SmartParking révolutionne la façon dont les conducteurs trouvent et réservent des places de stationnement. Notre plateforme offre une interface conviviale pour les clients et un système de gestion puissant pour les propriétaires de parkings.

![Vue d'ensemble](https://github.com/Abusooma/Smart-Parking/blob/main/.github/cap1.png)

## Fonctionnalités

- 🚗 Recherche de parkings par emplacement
- 📅 Système de réservation en temps réel
- 👤 Tableau de bord client pour la gestion des réservations
- 🏢 Interface d'administration pour les gérants de parking
- 📊 Rapports et analyses pour les propriétaires de parking
- 📱 Design responsive pour une utilisation mobile optimale

## Captures d'écran

### Page d'accueil
![Page d'accueil](https://github.com/Abusooma/Smart-Parking/blob/main/.github/cap1.png)
*Une interface intuitive pour commencer votre recherche de parking*

### Interface de réservation
![Recherche de parking](https://github.com/Abusooma/Smart-Parking/blob/main/.github/cap2.png)
*Trouvez facilement un parking près de votre destination*

### Tableau de bord
![Tableau de bord gérant](https://github.com/Abusooma/Smart-Parking/blob/main/.github/cap3.png)
*Outils puissants pour les gérants de parking*

## Installation

1. Clonez le dépôt :
   ```
   git clone https://github.com/votre-nom/smart-parking.git
   cd smart-parking
   ```

2. Créez un environnement virtuel et activez-le :
   ```
   python -m venv venv
   source venv/bin/activate  # Sur Windows, utilisez `venv\Scripts\activate`
   ```

3. Installez les dépendances :
   ```
   pip install -r requirements.txt
   ```

4. Effectuez les migrations :
   ```
   python manage.py migrate
   ```

5. Créez un superutilisateur :
   ```
   python manage.py createsuperuser
   ```

6. Lancez le serveur de développement :
   ```
   python manage.py runserver
   ```

## Utilisation

- Accédez à l'interface d'administration Django : `http://localhost:8000/admin/`
- Connectez-vous en tant que gérant pour ajouter et gérer vos parkings
- Les clients peuvent s'inscrire, rechercher des parkings et effectuer des réservations via l'interface principale

## Structure du projet

```
smart-parking/
│
├── manage.py
├── smart_parking/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── parking/
│   ├── migrations/
│   ├── templates/
│   ├── static/
│   ├── __init__.py
│   ├── admin.py
│   ├── models.py
│   ├── views.py
│   └── urls.py
│
├── users/
│   ├── migrations/
│   ├── templates/
│   ├── __init__.py
│   ├── admin.py
│   ├── models.py
│   ├── views.py
│   └── urls.py
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/
│   ├── base.html
│   └── ...
│
└── README.md
```

## Auteur

ABOUBACAR SOUMAH
