from django.contrib import admin

from .models import Person, Book, Genre, LinkType, Link

admin.site.register(Person)
admin.site.register(Book)
admin.site.register(Genre)
admin.site.register(Link)
admin.site.register(LinkType)
