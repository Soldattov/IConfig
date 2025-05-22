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

    
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email  # Используем email как логин
            user.is_verified = False     # Email пока не подтверждён
            user.save()

            # Генерируем шестизначный код подтверждения
            user.generate_verification_code()

            # Отправляем письмо с кодом подтверждения
            send_mail(
                'Подтверждение регистрации',
                f'Ваш код подтверждения: {user.verification_code}',
                'snitch_pc@mail.ru',  # либо "Имя сервиса <noreply@yourdomain.com>"
                [user.email],
                fail_silently=False,
            )

            # Вместо автоматического входа рендерим шаблон с флагом для открытия модального окна ввода кода
            return render(request, 'main/index.html', {
                'show_verification_modal': True,
                'email': user.email,  # Передаем email в скрытое поле
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
    return render(request, 'users/profile.html')

def verify_email_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        input_code = request.POST.get('verification_code')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return render(request, 'main/index.html', {
                'verify_error': 'Пользователь не найден!',
                'show_verification_modal': True
            })

        if user.verification_code == input_code:
            user.is_verified = True
            user.verification_code = None  # Очищаем код после подтверждения
            user.save()
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
    

    