from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Book)
admin.site.register(Student)
admin.site.register(Borrow)
admin.site.register(Subject)
admin.site.register(Shelf)
admin.site.register(Fine)
