from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def email_for_new_user(request, user, password):
    try:
        subject = "Bienvenue sur Smart Parking"
        html_message = render_to_string('smartparking/emails/send_email_to_new_user.html', {
            'user': user,
            'password': password,
            'login_url': request.build_absolute_uri('/login/')
        })
        plain_message = strip_tags(html_message)
        send_mail(subject, plain_message, settings.EMAIL_FROM, [user.email], html_message=html_message, fail_silently=True)
    except Exception as e:
        print(f"Erreur est survenu : {e}")


def email_confirm_reservation(request, user, reservation):
    try:
        subject = "Confirmation de votre réservation"
        context = {'reservation': reservation}
        html_message = render_to_string(
            'smartparking/emails/email_confirm_reservation.html', context)
        plain_message = strip_tags(html_message)
        send_mail(subject, plain_message, settings.EMAIL_FROM, [
                  user.email], html_message=html_message, fail_silently=False)
    except Exception as e:
        print(f'Erreur lors de l\'envoi de l\'e-mail : {e}')
