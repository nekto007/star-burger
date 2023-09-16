from rest_framework.serializers import ModelSerializer
from django.db import transaction
from .models import Order, OrderElements


class OrderItemSerializer(ModelSerializer):

    class Meta:
        model = OrderElements
        fields = ['id', 'product', 'quantity']


class OrderSerializer(ModelSerializer):

    products = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'firstname', 'lastname', 'phonenumber', 'address', 'products']

    @transaction.atomic
    def create(self, validated_data):
        order = Order.objects.create(
            phonenumber=validated_data['phonenumber'],
            firstname=validated_data['firstname'],
            lastname=validated_data['lastname'],
            address=validated_data['address'],
        )
        products = validated_data['products']

        elements = [OrderElements(
            order=order,
            price=fields['product'].price,
            **fields
        ) for fields in products]
        OrderElements.objects.bulk_create(elements)

        return order
