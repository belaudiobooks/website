from django.core.management import call_command
from django.test import SimpleTestCase
from books import models


class SeedDbTestCase(SimpleTestCase):
    databases = "__all__"

    def tearDown(self):
        call_command("flush", "--noinput")

    def test_seeding_works(self):
        call_command("flush", "--noinput")
        call_command("seed_db")
        # Sanity check that DB contains some data.
        self.assertGreater(models.Book.objects.count(), 10)
        self.assertGreater(models.Person.objects.count(), 2)
        self.assertGreater(models.Narration.objects.count(), 10)
        self.assertGreater(models.Link.objects.count(), 10)
        self.assertGreater(models.LinkType.objects.count(), 3)
        self.assertGreater(models.Publisher.objects.count(), 1)
