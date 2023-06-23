import datetime
from typing import Any, Dict
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
        if reason == 'no_tags':
            return queryset.annotate(num_tags=Count('tag')).filter(num_tags=0)
        if reason == 'no_translation':
            return queryset.filter(title_ru__exact='')
        raise ValueError(f'unknown incomplete_reason: {reason}')


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title', )}
    list_filter = (IncompleteBookListFilter, 'authors', 'title', 'promoted')
    list_display = ('title', 'get_book_authors', 'promoted')
    list_per_page = 1000
    autocomplete_fields = ['authors', 'translators']
    search_fields = ['title']

    class Media:
        js = ('js/admin.js', )

    @display(description='authors')
    def get_book_authors(self, obj):
        return ', '.join([str(person.name) for person in obj.authors.all()])


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name', )}


@admin.register(Link)
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
            'no_date_of_birth': 'Missing date of birth',
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
        if reason == 'no_date_of_birth':
            return queryset.filter(date_of_birth__isnull=True)
        raise ValueError(f'unknown incomplete_reason: {reason}')


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name', )}
    list_filter = (IncompletePersonListFilter, )
    ordering = ['slug']
    list_per_page = 1000
    search_fields = ['name']

    class Media:
        js = ('js/admin.js', )


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


class IncompleteLinksSetFilter(admin.SimpleListFilter):
    '''Filter that shows narration that have incomplete links.'''
    title = 'incomplete link set'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'incomplete_link'

    def lookups(self, request, model_admin):
        queryset = model_admin.get_queryset(request)
        reasons = {
            'no_google_play': 'Missing Google Play',
            'no_audiobooks_com': 'Missing audiobooks.com',
            'no_spotify': 'Missing Spotify',
            'no_apple_books': 'Missing Apple Books',
            'no_duration': 'Missing duration',
        }
        return [(
            key,
            f'{value} ({self._get_narrations_for_reason(queryset, key).count()})'
        ) for key, value in reasons.items()]

    def queryset(self, request, queryset):
        return self._get_narrations_for_reason(queryset, self.value())

    def _get_narrations_for_reason(self, queryset, reason):
        if reason is None:
            return queryset.filter()
        # We assume that all books in stores that are present on bookmate will
        # also be present on other stores eventually.
        if reason == 'no_google_play':
            return queryset.filter(
                links__url_type__name='rakuten_kobo').exclude(
                    links__url_type__name='google_play_books')
        if reason == 'no_audiobooks_com':
            return queryset.filter(
                links__url_type__name='rakuten_kobo').exclude(
                    links__url_type__name='audiobooks_com')
        if reason == 'no_spotify':
            return queryset.filter(
                links__url_type__name='rakuten_kobo').exclude(
                    links__url_type__name='spotify_podcast')
        if reason == 'no_apple_books':
            return queryset.filter(
                links__url_type__name='rakuten_kobo').exclude(
                    links__url_type__name='apple_books')
        if reason == 'no_duration':
            return queryset.filter(duration__isnull=True)
        raise ValueError(f'unknown incomplete_reason: {reason}')


class LinkInlineAdmin(admin.StackedInline):
    model = Link
    can_delete = True


@admin.register(Narration)
class NarrationAdmin(admin.ModelAdmin):
    list_filter = (NarratorsCountFilter, IncompleteLinksSetFilter)
    list_display = ('uuid', 'get_narrators', 'book')
    inlines = [LinkInlineAdmin]
    list_per_page = 1000
    autocomplete_fields = ['narrators', 'book']
    change_form_template = ['admin/books/change_form_narration.html']

    @display(description='narrators')
    def get_narrators(self, obj):
        return ', '.join([str(person.name) for person in obj.narrators.all()])

    class Media:
        js = ('js/admin.js', )

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        self._add_link_types_regex(extra_context)
        return super().change_view(
            request,
            object_id,
            form_url,
            extra_context=extra_context,
        )

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        self._add_link_types_regex(extra_context)
        return super().add_view(
            request,
            form_url,
            extra_context=extra_context,
        )

    def _add_link_types_regex(self, extra_context: Dict[str, Any]):
        # Add mapping of link types ids to their url regex to client-side.
        # It will be used by JS to auto-detect type of a new link.
        link_types_regexes = []
        for link_type in LinkType.objects.all():
            if link_type.url_regex != '':
                link_types_regexes.append((link_type.id, link_type.url_regex))
        extra_context['link_types_regexes'] = link_types_regexes


admin.site.register(LinkType)
