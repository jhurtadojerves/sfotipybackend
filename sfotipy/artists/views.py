from django.shortcuts import render

# Create your views here.
from django.views.generic.detail import DetailView

from .models import Artist

class ArtistDetailView(DetailView):
	model = Artist
	context_object_name = 'artist'

	def get_template_names(self):
		return 'artist.html'
