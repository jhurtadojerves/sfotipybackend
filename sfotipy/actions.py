# # -*- coding: utf-8 -*-

# import csv
# import logging
# import tablib
# from datetime import datetime
# from django.db.models import Model
# from django.db.model.fields.files import FieldFile
# from unicodedata import normalize
# from django.core.exceptions import PermissionDenied
# from django.http import HttpResponse
# from django.template import Context, Template
# from django.conf import settings
# from django.core.urlresolvers import reverse

# def export_as_excel(modeladmin, request, queryset):
# 	if not request.user.is_staff:
# 		raise PermissionDenied
# 	opts = modeladmin.mode._meta
# 	response = HttpResponse(mimetype = 'text/csv; charset=utf-8')
# 	response['Content-Disposition'] = 'attachment; filename=%s.xls' %


