from random import choice
from django.shortcuts import redirect
paises = ['Colombia', 'Peru', 'Chile',]

def de_donde_vengo(request):
	return choice(paises)

class PaisMiddleware():
	def process_request(self,request):
		pais = de_donde_vengo(request)
		if pais== 'Mexico':
			return redirect('http://mejorando.la')