from random import choice

frases = ['lol','hola','ke','ase']

from tracks.models import Track
def basico(request):
	tracks = Track.objects.all()
	track = None	
	for t in tracks:
		if request.path == t.get_absolute_url():
			track = t
			break
	return {'titulo': choice(frases), 'tracks': tracks, 'selected_track': track}