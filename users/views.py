from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import UserRegistrationForm, UserLoginForm
from django.contrib.auth.decorators import login_required
from .models import CustomUser
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import LoginView
from main.models import SavedConfiguration
import random
import smtplib

    
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        email = request.POST.get('email')
        
        # Если пользователь с таким email уже существует, выводим нужное сообщение
        if CustomUser.objects.filter(email=email).exists():
            return render(request, 'main/index.html', {
                'form': form,
                'register_error': "Пользователь с таким email уже существует.",
                'show_register_modal': True
            })
            
        if form.is_valid():
            registration_data = form.cleaned_data

            # Генерируем случайный шестизначный код подтверждения
            verification_code = str(random.randint(100000, 999999))
            
            # Сохраняем регистрационные данные и код подтверждения в сессии
            request.session['registration_data'] = registration_data
            request.session['verification_code'] = verification_code

            try:
                # Отправляем письмо с кодом подтверждения
                send_mail(
                    'Подтверждение регистрации',
                    f'Ваш код подтверждения: {verification_code}',
                    'snitch_pc@mail.ru',  # либо "Имя сервиса <noreply@yourdomain.com>"
                    [email],
                    fail_silently=False,
                )
            except (smtplib.SMTPDataError, smtplib.SMTPRecipientsRefused) as e:
                return render(request, 'main/index.html', {
                    'form': form,
                    'register_error': "Такой электронной почты не существует.",
                    'show_register_modal': True
                })

            # Если письмо отправилось успешно, отображаем окно ввода кода подтверждения
            return render(request, 'main/index.html', {
                'show_verification_modal': True,
                'email': email,
            })
        else:
            return render(request, 'main/index.html', {
                'form': form,
                'register_error': "Пожалуйста, проверьте введённые данные!",
                'show_register_modal': True
            })
    else:
        return redirect('main:index')
    
def login_view(request):
    error = None
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('main:index')
        else:
            error = "Неверный логин или пароль."
    else:
        return redirect('main:index')

    return render(request, 'main/index.html', {'login_error': error})
    
def logout_view(request):
    logout(request)
    return redirect('main:index')

@login_required
def profile_view(request):
    user = request.user

    # Если форма отправлена (POST) — обновляем только имя пользователя
    if request.method == 'POST':
        first_name = request.POST.get('first_name')

        if first_name and first_name != user.first_name:
            user.first_name = first_name
            user.save()
            # Обновляем сессионный хеш, чтобы изменения вступили в силу
            update_session_auth_hash(request, user)

        # Перенаправляем пользователя на страницу профиля для отражения изменений
        return redirect('profile')

    # Исходная логика: получение конфигураций и вывод в консоль
    print('Получение профиля пользователя:', user.username)
    configs = SavedConfiguration.objects.filter(user=user).prefetch_related('components')
    print('Найдено конфигураций:', configs.count())
    for config in configs:
        print(f'Конфигурация: {config.name}, ID: {config.id}, Компонентов: {config.components.count()}')
        for component in config.components.all():
            print(f'  - {component.component_type}: {component.name} ({component.price} ₽)')

    context = {
        'user': user,
        'configurations': configs,
        'page_title': 'Профиль'
    }
    return render(request, 'users/profile.html', context)

def verify_email_view(request):
    if request.method == 'POST':
        input_code = request.POST.get('verification_code')
        # Получаем данные регистрации и код из сессии
        registration_data = request.session.get('registration_data')
        session_code = request.session.get('verification_code')

        if not registration_data or not session_code:
            return render(request, 'main/index.html', {
                'verify_error': 'Сессия регистрации устарела, пожалуйста, зарегистрируйтесь заново.',
                'show_register_modal': True
            })

        email = registration_data.get('email', '')
        if input_code == session_code:
            # Создаем пользователя, передавая email как для email, так и для username
            password = registration_data.get('password1')  # убедитесь, что в форме это имя поля для пароля
            user = CustomUser.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=registration_data.get('first_name'),
                # Если у вас есть другие обязательные поля, добавьте их сюда
            )
            user.is_verified = True
            user.save()

            # Очистка данных регистрации из сессии
            del request.session['registration_data']
            del request.session['verification_code']

            login(request, user)
            return redirect('main:index')
        else:
            return render(request, 'main/index.html', {
                'verify_error': 'Неверный код!',
                'show_verification_modal': True,
                'email': email,
            })
    return redirect('main:index')

@require_POST
@login_required
def delete_account(request):
    try:
        # Удаляем учетную запись текущего пользователя
        user = request.user
        user.delete()
        # Выход пользователя из системы
        logout(request)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
@require_POST
@login_required
def verify_current_password(request):
    data = json.loads(request.body)
    input_password = data.get("current_password")
    user = request.user
    # Функция check_password сравнивает введённый пароль с хэшем в БД
    if user.check_password(input_password):
        return JsonResponse({"valid": True})
    else:
        return JsonResponse({"valid": False})
    
@require_POST
@login_required
def change_password(request):
    try:
        data = json.loads(request.body)
        current_password = data.get("current_password")
        new_password = data.get("new_password")
        user = request.user

        # Проверяем, корректен ли текущий пароль
        if not user.check_password(current_password):
            return JsonResponse({"success": False, "error": "Неверный текущий пароль"}, status=400)

        # Простой пример проверки нового пароля: не менее 8 символов
        if len(new_password) < 8:
            return JsonResponse({"success": False, "error": "Новый пароль должен быть не менее 8 символов"}, status=400)

        # Устанавливаем новый пароль
        user.set_password(new_password)
        user.save()

        # Обновляем сессионный хеш, чтобы пользователь не был разлогинен после смены пароля
        update_session_auth_hash(request, user)

        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
    

