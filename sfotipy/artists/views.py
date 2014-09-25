from django.shortcuts import render

# Create your views here.
from django.views.generic.detail import DetailView

from .models import Artist


class ArtistDetailView(DetailView):
	model = Artist
	context_object_name = 'fav_artist'
	template_name = 'artist.html'

# class ArtistListView(ListView):
# 	model = Artist
# 	context_object_name = 'artist'
# 	template_name = 'artist.html'

from rest_framework import viewsets
from .serializers import ArtistSerializers

class ArtistViewSet(viewsets.ModelViewSet):
	model = Artist
	filter_fields = ('id',)
	paginate_by = 1
	serializer_class = ArtistSerializers