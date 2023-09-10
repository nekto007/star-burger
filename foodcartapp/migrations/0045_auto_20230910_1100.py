# Generated by Django 3.2.15 on 2023-09-10 11:00

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0044_auto_20230910_1058'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='called_at',
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now, null=True, verbose_name='дата звонка'),
        ),
        migrations.AlterField(
            model_name='order',
            name='created_at',
            field=models.DateTimeField(blank=True, db_index=True, default=django.utils.timezone.now, verbose_name='дата создания заказа'),
        ),
        migrations.AlterField(
            model_name='order',
            name='delivered_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='дата доставки'),
        ),
    ]
