# Generated by Django 3.2.15 on 2023-09-16 14:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0053_alter_orderelements_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderelements',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_elements', to='foodcartapp.order', verbose_name='заказ'),
        ),
    ]
