# Generated by Django 5.1 on 2024-08-19 23:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smartparking', '0010_reservation_access_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='Matricule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('matricule', models.CharField(max_length=30)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='smartparking.client')),
            ],
        ),
    ]
