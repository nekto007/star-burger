from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Sum
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class OrderQuerySer(models.QuerySet):
    def order_price(self):
        return self.annotate(total_price=Sum(F('products__quantity') * F('products__product__price')))


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class Order(models.Model):
    class ChoicesStatus(models.TextChoices):
        COMPLETED = 'Завершен', 'Завершен'
        ON_MY_WAY = 'В пути', 'В пути'
        PROGRESS = 'Готовится', 'Готовится'
        ACCEPTED = 'Принят', 'Принят'
        RAW = 'Необработанный', 'Необработанный'

    class ChoicesPayment(models.TextChoices):
        ELECTRONIC_MONEY = 'Электронные', 'Электронные'
        CASH = 'Наличные', 'Наличные'
        NOT_SPECIFIED = 'Не указан', 'Не указан'

    address = models.CharField(
        'адрес',
        max_length=100,
    )
    firstname = models.CharField(
        'имя',
        max_length=50
    )
    lastname = models.CharField(
        'фамилия',
        max_length=50
    )
    phonenumber = PhoneNumberField(
        'контактный телефон',
        region='RU',
    )
    status = models.CharField(
        'статус',
        default=ChoicesStatus.RAW,
        max_length=30,
        choices=ChoicesStatus.choices,
        db_index=True
    )
    comment = models.TextField(
        'комментарий',
        blank=True
    )
    created_at = models.DateTimeField(
        'дата создания заказа',
        default=timezone.now,
        blank=True,
        db_index=True
    )
    called_at = models.DateTimeField(
        'дата звонка',
        default=timezone.now,
        null=True,
        db_index=True
    )
    delivered_at = models.DateTimeField(
        'дата доставки',
        blank=True,
        null=True,
        db_index=True
    )
    payment = models.CharField(
        'способ оплаты',
        default=ChoicesPayment.NOT_SPECIFIED,
        max_length=30,
        choices=ChoicesPayment.choices,
        db_index=True
    )
    assigned_restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='готовит ресторан',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def process_order(self):
        menu_items = self.products.all()
        available_restaurants = []

        for item in menu_items:
            if item.product.menu_items.filter(availability=True).exists():
                available_restaurants.append(item.product.menu_items.first().restaurant)

        return list(set(available_restaurants))

    def get_assigned_restaurant(self):
        if self.assigned_restaurant:
            return self.assigned_restaurant.name
        else:
            return None

    objects = OrderQuerySer.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f"{self.lastname} {self.firstname}"


class OrderElements(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='products',
        verbose_name="заказ",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='order_elements',
        verbose_name='товар',
    )
    quantity = models.IntegerField(
        'Количество продуктов в заказе',
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        db_index=True)
    price = models.DecimalField(
        'цена',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'элемент заказа'
        verbose_name_plural = 'элементы заказа'
        unique_together = [
            ['order', 'product']
        ]

    def __str__(self):
        return f"{self.product.name} {self.order.lastname} {self.order.firstname} {self.order.address}"
