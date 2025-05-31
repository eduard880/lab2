from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Book, User
from django.contrib.auth import get_user_model
class BookForm(forms.ModelForm):
    """
    Форма для создания и редактирования книг
    """
    class Meta:
        model = Book
        fields = ['title', 'author', 'price', 'description', 'publication_date', 'isbn']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'publication_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Название книги',
            'author': 'Автор',
            'price': 'Цена (руб)',
            'description': 'Описание',
            'publication_date': 'Дата публикации',
            'isbn': 'ISBN',
        }

class RegisterForm(UserCreationForm):
    """
    Форма регистрации пользователя с дополнительными полями
    """
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': 'Логин',
            'email': 'Электронная почта',
            'first_name': 'Имя',
            'password1': 'Пароль',
            'password2': 'Подтверждение пароля',
        }





User = get_user_model()
class LoginForm(forms.Form):

    """
    Форма входа в систему
    """
    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def get_user(self):
        return self.user_cache  # Возвращает аутентифицированного пользователя

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CheckoutForm(forms.Form):
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))



class CheckoutForm(forms.Form):
    shipping_address = forms.CharField(
        label='Адрес доставки',
        widget=forms.Textarea(attrs={'rows': 3}),
        required=True
    )
    phone = forms.CharField(
        label='Телефон',
        max_length=20,
        required=True
    )
    notes = forms.CharField(
        label='Примечания к заказу',
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False
    )