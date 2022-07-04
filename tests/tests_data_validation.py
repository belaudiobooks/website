from os import path
from typing import List
from queue import Queue
from threading import Thread
from django.test import TransactionTestCase
import requests

from books import models


class Worker(Thread):
    ''' Thread executing tasks from a given tasks queue '''

    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as exc:
                # An exception happened in this thread
                print(exc, args)
            finally:
                # Mark this task as done, whether an exception happened or not
                self.tasks.task_done()


class DataValidationTests(TransactionTestCase):
    '''Tests that validate data.'''

    fixtures = ['data/data.json']

    def _verify_books_covers_valid(self):
        for book in models.Book.objects.all():
            cover = book.cover_image
            if cover.name == '':
                continue
            assert path.exists(
                cover.path
            ), f'For book {book.title} did not find image {cover.path}'

    def _verify_link_type_icons_exist(self):
        for link_type in models.LinkType.objects.all():
            icon_path = link_type.icon.path
            assert path.exists(
                icon_path
            ), f'For link type {link_type.name} did not find icon {icon_path}'

    def _verify_people_photos_valid(self):
        for person in models.Person.objects.all():
            photo = person.photo
            if photo.name == '':
                continue
            assert path.exists(
                photo.path
            ), f'For person {person.name} did not find image {photo.path}'

    def test_files_present(self):
        self._verify_books_covers_valid()
        self._verify_link_type_icons_exist()
        self._verify_people_photos_valid()

    def test_data_complete(self):
        for book in models.Book.objects.all():
            self.assertNotEqual(book.narrations.count(),
                                0,
                                msg=f'Book {book.title} has no narrations.')
        for narration in models.Narration.objects.all():
            self.assertNotEqual(
                narration.links.count(),
                0,
                msg=f'Narration {narration.uuid} has no links.')
        for person in models.Person.objects.all():
            self.assertNotEqual(person.books_authored.count() +
                                person.narrations.count() +
                                person.books_translated.count(),
                                0,
                                msg=f'Person {person.name} has no books.')

    def test_russian_translations_present(self):
        for person in models.Person.objects.all():
            self.assertNotEqual(person.name_ru,
                                '',
                                msg=f'Missing name_ru for {person.name}')
        for book in models.Book.objects.all():
            self.assertNotEqual(book.title_ru,
                                '',
                                msg=f'Missing title_ru for {book.title}')

    def test_links_match_link_type_regex(self):
        for link in models.Link.objects.all():
            if link.url_type.url_regex == '':
                continue
            self.assertRegex(link.url, link.url_type.url_regex)

    def test_verify_links_return_200(self):
        self.maxDiff = 10000
        session = requests.session()
        statuses: List[tuple[str, requests.Response]] = []
        get = lambda url: statuses.append((url, session.head(url, timeout=20)))
        tasks = Queue()
        for _ in range(40):
            Worker(tasks)

        for link in models.Link.objects.all():  # type: models.Link
            # skip kobo as it doesn't responde to robot-like requests.
            # skip soundcloud as it responds with 429.
            # skip litres as they return 403 when test runs from github.
            if link.url_type.name == 'rakuten_kobo' or link.url.startswith(
                    'https://soundcloud.com'
            ) or link.url_type.name == 'litres':
                continue
            tasks.put((get, (link.url, ), {}))
        tasks.join()
        errors = []
        for url, response in statuses:
            # castbox returns 302.
            # all other should return 200.
            if response.status_code != 200 and response.status_code != 302:
                errors.append((url, response.status_code))
        self.assertListEqual(errors, [])