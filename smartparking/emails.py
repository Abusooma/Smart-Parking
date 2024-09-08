from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


def clean_email(email):
    try:
        validate_email(email)
        return email.strip()
    except ValidationError as e:
        raise ValueError("Adresse email invalide") from e



def email_for_new_user(request, user, password, path_template):
    try:
        subject = "Smart"
        html_message = render_to_string(path_template, {
            'user': user,
            'password': password,
            'login_url': request.build_absolute_uri('/login/')
        })
        plain_message = strip_tags(html_message)
        send_mail(
            subject,
            plain_message,
            settings.EMAIL_HOST_USER,
            [clean_email(user.email)],
            html_message=html_message
        )
    except Exception as e:
        print(str(e))


def email_confirm_reservation(request, user, reservation):
    try:
        validated_email = clean_email(user.email)
        subject = "Confirmation de votre réservation"
        context = {'reservation': reservation}
        html_message = render_to_string(
            'smartparking/emails/email_confirm_reservation.html', context)
        plain_message = strip_tags(html_message)

        send_mail(subject, plain_message, settings.EMAIL_HOST_USER, [validated_email], html_message=html_message, fail_silently=True)
    except Exception as e:
        print("Erreur")
        send_mail(subject, plain_message, settings.EMAIL_HOST_USER, [validated_email], html_message=html_message)
    except Exception as e:
        raise ValueError(e) from e

