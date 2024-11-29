# Generated by Django 5.1.2 on 2024-11-05 05:23

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('RestConnectApp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='mesa',
            name='pedido_info',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='pedido',
            name='fecha_pedido',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='tipousuario',
            name='rol',
            field=models.CharField(max_length=50),
        ),
    ]