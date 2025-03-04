import requests
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login, views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from geopy import distance

from foodcartapp.models import Order, Product, Restaurant
from geocoder.models import GeocodeData


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    try:
        response.raise_for_status()
        found_places = response.json()['response']['GeoObjectCollection']['featureMember']
    except requests.exceptions.RequestException:
        return None

    if found_places:
        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
        return lon, lat


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    yandex_token = settings.YANDEX_TOKEN
    geocoder = GeocodeData.objects.all()
    order_items = Order.objects.exclude(status='Завершен').order_price()
    for item in order_items:
        item.available_restaurants = item.process_order()
        item.restaurants_with_distance = []

        geo_client = fetch_coordinates(yandex_token, item.address)
        if geo_client is None:
            continue

        geo_client_db, _ = GeocodeData.objects.get_or_create(
            address=item.address,
            defaults={'lat': geo_client[1], 'lon': geo_client[0]}
        )

        for restaurant in item.available_restaurants:
            geo_restaurant = geocoder.filter(address=restaurant.address).values('lat', 'lon').first()
            if not geo_restaurant or not geo_client_db:
                continue

            geo_client_db, _ = GeocodeData.objects.get_or_create(
                address=item.address,
                defaults={'lat': geo_client[1], 'lon': geo_client[0]}
            )

            restaurant_coordinates = (geo_restaurant['lat'], geo_restaurant['lon'])
            client_coordinates = (geo_client_db.lat, geo_client_db.lon)

            distance_km = round(distance.distance(client_coordinates, restaurant_coordinates).km, 3)

            item.restaurants_with_distance.append({
                'restaurant': restaurant,
                'distance': distance_km
            })

        item.restaurants_with_distance.sort(key=lambda x: x['distance'])
    return render(request, template_name='order_items.html', context={
        'order_items': order_items
    })
