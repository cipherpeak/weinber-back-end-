from django.contrib import admin

from .models import Document, VisaDetails

# Register your models here.
admin.site.register(VisaDetails)
admin.site.register(Document)
