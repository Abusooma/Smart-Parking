# Generated by Django 5.1 on 2024-08-18 22:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smartparking', '0009_remove_gerant_date_embauche_alter_reservation_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='access_code',
            field=models.CharField(blank=True, max_length=7, null=True),
        ),
    ]
