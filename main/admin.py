from django.contrib import admin

# Register your models here.
from main.models import User, Variant, Question, Group

admin.site.register(User)
admin.site.register(Group)
admin.site.register(Variant)
admin.site.register(Question)
