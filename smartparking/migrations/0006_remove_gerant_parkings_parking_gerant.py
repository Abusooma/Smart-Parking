# Generated by Django 5.1 on 2024-08-16 13:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smartparking', '0005_reservation_is_cancel'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gerant',
            name='parkings',
        ),
        migrations.AddField(
            model_name='parking',
            name='gerant',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='smartparking.gerant'),
        ),
    ]
