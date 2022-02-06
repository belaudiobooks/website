from django.contrib import admin
from django.contrib.admin.decorators import display

from .models import Person, Book, Tag, LinkType, Link


class BookAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title', )}
    list_filter = ('authors', 'title', 'promoted')
    list_display = ('title', 'get_book_authors', 'promoted')

    @display(description='authors')
    def get_book_authors(self, obj):
        return ', '.join([str(person.name) for person in obj.authors.all()])


class LinkAdmin(admin.ModelAdmin):
    list_display = ('url', 'get_book', 'url_type')

    @display(description='authors')
    def get_book(self, obj):
        return obj.book


class PersonAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name', )}
    list_filter = ('name', )


admin.site.register(Person, PersonAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Tag)
admin.site.register(Link, LinkAdmin)
admin.site.register(LinkType)
