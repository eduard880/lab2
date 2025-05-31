from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Модель пользователя с расширенными полями и ролями
    """
    class Role(models.TextChoices):
        USER = 'user', 'Обычный пользователь'
        ADMIN = 'admin', 'Администратор'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER,
        verbose_name='Роль'
    )
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name='Адрес'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Город'
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Почтовый индекс'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Телефон'
    )

    def is_admin(self):
        return self.role == self.Role.ADMIN

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Book(models.Model):
    """
    Модель книги для магазина
    """
    title = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    author = models.CharField(
        max_length=100,
        verbose_name='Автор'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    publication_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата публикации'
    )
    isbn = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='ISBN'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    def __str__(self):
        return f"{self.title} - {self.author}"

    class Meta:
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['author']),
        ]


class Cart(models.Model):
    """
    Модель корзины пользователя
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='Пользователь'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )


    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return f"Корзина #{self.id} пользователя {self.user.username}"

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        ordering = ['-created_at']


class CartItem(models.Model):
    """
    Модель элемента корзины
    """

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Корзина'
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        verbose_name='Книга'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name='Количество'
    )


    def get_total_price(self):
        return self.quantity * self.book.price

    def __str__(self):
        return f"{self.quantity} x {self.book.title} (корзина #{self.cart.id})"

    class Meta:
        verbose_name = 'Элемент корзины'
        verbose_name_plural = 'Элементы корзины'
        unique_together = ['cart', 'book']  # Предотвращает дублирование книг в корзине


class Order(models.Model):
    """
    Модель заказа
    """
    STATUS_CHOICES = [
        ('pending', 'В обработке'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Пользователь'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Общая стоимость'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    shipping_address = models.TextField(
        verbose_name='Адрес доставки',
        blank=True,
        null=True
    )
    phone = models.CharField(
        max_length=20,
        verbose_name='Телефон',
        blank=True,
        null=True
    )

    # Дополнительные методы
    def __str__(self):
        return f"Заказ #{self.id} ({self.get_status_display()})"

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return f"Заказ #{self.id} ({self.get_status_display()})"

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]


class OrderItem(models.Model):
    """
    Модель элемента заказа
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ'
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.PROTECT,
        verbose_name='Книга'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name='Количество'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена за единицу'
    )

    def get_total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.book.title} (заказ #{self.order.id})"

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

