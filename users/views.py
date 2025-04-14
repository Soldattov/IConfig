from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import UserRegistrationForm, UserLoginForm
from django.contrib.auth.decorators import login_required

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email  
            user.save()
            login(request, user)
            return redirect('main:index')
        else:
            return render(request, 'main/index.html', {'form': form, 'register_error': "Пожалуйста, проверьте введённые данные!"})
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