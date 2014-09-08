from django.shortcuts import render
from django.contrib.auth import authenticate
from django.contrib.auth import login

from .forms import UserCreationEmailForm, EmailAuthenticationForm


def signup(request):
	form = UserCreationEmailForm(request.POST or None)

	if form.is_valid():
		user = form.save()
		user_cache= authenticate(email=request.POST.get('email'), password= request.POST.get('password1'))
		login(request, user_cache)
		
		#crear perfil de usuario
		#rediccionar al home

	return render(request, 'signup.html', {'form': form} )

def signin(request):
	form = EmailAuthenticationForm(request.POST or None)

	if form.is_valid():
		login(request, form.get_user())
		#rediccionar al home
		
	return render(request, 'signin.html', {'form':form})
