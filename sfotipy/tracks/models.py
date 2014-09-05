from django.db import models

# Create your models here.
class Track(models.Model):
	"""docstring for Track"""
	def __init__(self, arg):
		super(Track, self).__init__()
		self.arg = arg
		