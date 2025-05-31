from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from .models import Book, User, Cart, CartItem, Order, OrderItem
from .forms import BookForm, RegisterForm, LoginForm, UserProfileForm, CheckoutForm
from django.db import transaction
from django.http import JsonResponse
from django.db import connection
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q

def book_list(request):
    """
    Отображение списка всех книг с пагинацией
    Доступно всем пользователям (включая неавторизованных)
    """
    # Получаем все книги, отсортированные по дате создания (новые сначала)
    book_list = Book.objects.all().order_by('-created_at')

    # Создаем пагинатор - 10 книг на страницу (можно изменить)
    paginator = Paginator(book_list, 10)

    # Получаем номер текущей страницы из GET-параметра
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'user': request.user,
    }

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        context['cart'] = cart

    return render(request, 'books/book_list.html', context)

def register_view(request):
    """
    Регистрация нового пользователя
    """
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('book_list')
        else:
            print("\n=== FORM ERRORS ===")
            print("Non-field errors:", form.non_field_errors())
            for field in form:
                if field.errors:
                    print(f"Field '{field.name}': {field.errors}")
            print("=== END FORM ERRORS ===\n")
            print("форма невалидна")
            return render(request, 'books/register.html', {'form': form})

    else:
        form = RegisterForm()
    return render(request, 'books/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('book_list')
            else:
                form.add_error(None, "Неверный логин или пароль")
    else:
        form = LoginForm()
    return render(request, 'books/login.html', {'form': form})

def logout_view(request):
    """
    Выход из системы
    """
    logout(request)
    return redirect('book_list')

# Декоратор для проверки административных прав
def admin_required(view_func):
    """
    Декоратор для проверки, что пользователь является администратором
    """
    return user_passes_test(
        lambda u: u.is_authenticated and u.is_admin(),
        login_url='book_list'
    )(view_func)

@login_required(login_url='login')
def add_book(request):
    """
    Добавление новой книги (доступно авторизованным пользователям)
    """
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'books/book_form.html', {
        'form': form,
        'title': 'Добавить книгу'
    })

@admin_required
def edit_book(request, pk):
    """
    Редактирование книги (доступно только администраторам)
    """
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('book_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'books/book_form.html', {
        'form': form,
        'title': 'Редактировать книгу'
    })

@admin_required
def delete_book(request, pk):
    """
    Удаление книги (доступно только администраторам)
    """
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        return redirect('book_list')
    return render(request, 'books/book_confirm_delete.html', {'book': book})


# Добавить новые view-функции

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'books/profile.html', {'form': form})


@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    total = sum(item.book.price * item.quantity for item in cart.items.all())
    return render(request, 'books/cart.html', {'cart': cart, 'total': total})


@login_required
def add_to_cart(request, pk):
    book = get_object_or_404(Book, pk=pk)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, book=book)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('book_list')




@login_required
def orders_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'books/orders.html', {'orders': orders})


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)

    if not cart.items.exists():
        return redirect('cart')

    # Правильно считаем общую сумму с учётом количества
    total = sum(item.book.price * item.quantity for item in cart.items.all())

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    order = Order.objects.create(
                        user=request.user,
                        total_price=total,
                        shipping_address=form.cleaned_data['shipping_address'],
                        phone=form.cleaned_data['phone'],
                        status='pending'
                    )

                    # Сохраняем все товары с их количеством
                    for item in cart.items.all():
                        OrderItem.objects.create(
                            order=order,
                            book=item.book,
                            quantity=item.quantity,  # Важно: сохраняем количество
                            price=item.book.price
                        )

                    cart.items.all().delete()
                    messages.success(request, 'Заказ успешно оформлен!')
                    return redirect('order_detail', order_id=order.id)

            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
    else:
        form = CheckoutForm(initial={
            'shipping_address': request.user.address,
            'phone': request.user.phone
        })

    return render(request, 'books/checkout.html', {
        'form': form,
        'cart': cart,
        'total': total,
        'items': cart.items.all()  # Передаём все товары с их количеством
    })

@login_required
def orders_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'books/orders.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'books/order_detail.html', {'order': order})

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, "Товар удалён из корзины")
    return redirect('cart')


@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        new_quantity = int(request.POST.get('quantity', 1))
        if new_quantity > 0:
            cart_item.quantity = new_quantity
            cart_item.save()
            messages.success(request, "Количество обновлено")
        else:
            cart_item.delete()
            messages.success(request, "Товар удалён из корзины")
    return redirect('cart')


@login_required
@csrf_protect
def safe_search(request):
    search_term = request.GET.get('q', '')

    # Безопасный запрос через ORM
    results = Book.objects.filter(title__icontains=search_term)

    # Если необходимо использовать raw SQL (не рекомендуется без необходимости)
    with connection.cursor() as cursor:
        # Параметризованный запрос
        cursor.execute("SELECT * FROM books_book WHERE title LIKE %s", [f'%{search_term}%'])
        rows = cursor.fetchall()

    return render(request, 'search_results.html', {'results': results})


def check_username(request):
    username = request.GET.get('username', '')
    data = {
        'is_taken': User.objects.filter(username__iexact=username).exists()
    }
    return JsonResponse(data)


def book_list(request):
    books = Book.objects.all().order_by('-created_at')

    # Фильтрация по поисковому запросу
    search_query = request.GET.get('search', '')
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query)
        )

    # Фильтрация по цене
    min_price = request.GET.get('min_price')
    if min_price:
        books = books.filter(price__gte=min_price)

    max_price = request.GET.get('max_price')
    if max_price:
        books = books.filter(price__lte=max_price)

    # Пагинация
    per_page = request.GET.get('per_page', 10)
    paginator = Paginator(books, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'user': request.user,
    }

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        context['cart'] = cart

    return render(request, 'books/book_list.html', context)

