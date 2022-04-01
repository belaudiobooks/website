import datetime
from django.contrib import admin
from django.contrib.admin.decorators import display
from django.db.models import Count

from .models import Person, Book, Tag, LinkType, Link, Narration


class IncompleteBookListFilter(admin.SimpleListFilter):
    '''Filter that shows books that have incomplete data like missing description or cover.'''
    title = 'incomplete data'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'incomplete_reason'

    def lookups(self, request, model_admin):
        queryset = model_admin.get_queryset(request)
        reasons = {
            'no_description': 'Missing description',
            'no_cover': 'Missing cover',
            'no_duration': 'Missing duration',
            'no_tags': 'Missing tags',
            'no_translation': 'Missing russian title',
        }
        return [
            (key,
             f'{value} ({self._get_books_for_reason(queryset, key).count()})')
            for key, value in reasons.items()
        ]

    def queryset(self, request, queryset):
        return self._get_books_for_reason(queryset, self.value())

    def _get_books_for_reason(self, queryset, reason):
        if reason is None:
            return queryset
        if reason == 'no_description':
            return queryset.filter(description__exact='')
        if reason == 'no_cover':
            return queryset.filter(cover_image__exact='')
        if reason == 'no_duration':
            zero_duration = datetime.timedelta(seconds=0)
            return queryset.filter(duration_sec__exact=zero_duration)
        if reason == 'no_tags':
            return queryset.annotate(num_tags=Count('tag')).filter(num_tags=0)
        if reason == 'no_translation':
            return queryset.filter(title_ru__exact='')
        raise ValueError(f'unknown incomplete_reason: {reason}')


class BookAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title', )}
    list_filter = (IncompleteBookListFilter, 'authors', 'title', 'promoted')
    list_display = ('title', 'get_book_authors', 'promoted')
    list_per_page = 1000

    @display(description='authors')
    def get_book_authors(self, obj):
        return ', '.join([str(person.name) for person in obj.authors.all()])


class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name', )}


class LinkAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'url_type', 'get_book', 'get_narrators', 'url')
    list_per_page = 1000

    @display(description='book')
    def get_book(self, obj):
        return obj.narration.book

    @display(description='narrators')
    def get_narrators(self, obj):
        if obj.narration:
            narrators = ', '.join(
                [str(person.name) for person in obj.narration.narrators.all()])
            return narrators
        else:
            return 'None'


class IncompletePersonListFilter(admin.SimpleListFilter):
    '''Filter that shows people that have incomplete data like missing description or photo.'''
    title = 'incomplete data'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'incomplete_reason'

    def lookups(self, request, model_admin):
        queryset = model_admin.get_queryset(request)
        reasons = {
            'no_description': 'Missing description',
            'no_photo': 'Missing photo',
            'no_translation': 'Missing russian name',
        }
        return [
            (key,
             f'{value} ({self._get_people_for_reason(queryset, key).count()})')
            for key, value in reasons.items()
        ]

    def queryset(self, request, queryset):
        return self._get_people_for_reason(queryset, self.value())

    def _get_people_for_reason(self, queryset, reason):
        if reason is None:
            return queryset
        if reason == 'no_description':
            return queryset.filter(description__exact='')
        if reason == 'no_photo':
            return queryset.filter(photo__exact='')
        if reason == 'no_translation':
            return queryset.filter(name_ru__exact='')
        raise ValueError(f'unknown incomplete_reason: {reason}')


class PersonAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name', )}
    list_filter = (IncompletePersonListFilter, )
    ordering = ['slug']
    list_per_page = 1000


class NarratorsCountFilter(admin.SimpleListFilter):
    '''Filter that shows number of narrators for narrations.'''
    title = 'number of narrators'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'narrators_count'

    def lookups(self, request, model_admin):
        queryset = model_admin.get_queryset(request)
        return [(
            count,
            f'{count} ({self._get_books_narrators_count(queryset, count).count()})'
        ) for count in [0, 1, 2, 3, 5, 6]]

    def queryset(self, request, queryset):
        return self._get_books_narrators_count(queryset, self.value())

    def _get_books_narrators_count(self, queryset, count):
        if count is None:
            return queryset
        return queryset.annotate(num_narrators=Count('narrators')).filter(
            num_narrators=int(count))


class LinkInlineAdmin(admin.StackedInline):
    model = Link
    can_delete = True


class NarrationAdmin(admin.ModelAdmin):
    list_filter = (NarratorsCountFilter, )
    list_display = ('uuid', 'book', 'get_narrators')
    inlines = [LinkInlineAdmin]
    list_per_page = 1000

    @display(description='narrators')
    def get_narrators(self, obj):
        return ', '.join([str(person.name) for person in obj.narrators.all()])


admin.site.register(Person, PersonAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(LinkType)
admin.site.register(Narration, NarrationAdmin)
