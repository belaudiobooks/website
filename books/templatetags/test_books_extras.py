import unittest
from books.templatetags import books_extras


class BooksExtrasTestCase(unittest.TestCase):
    def test_youtube_embed_link_good(self):
        self.assertEqual(
            books_extras.youtube_embed_link("https://youtu.be/ke7Gvn1UUeU"),
            "https://www.youtube.com/embed/ke7Gvn1UUeU",
        )
        self.assertEqual(
            books_extras.youtube_embed_link(
                "https://www.youtube.com/watch?v=RHC3SQFCWB4"
            ),
            "https://www.youtube.com/embed/RHC3SQFCWB4",
        )
        self.assertEqual(
            books_extras.youtube_embed_link("https://youtube.com/watch?v=RHC3SQFCWB4"),
            "https://www.youtube.com/embed/RHC3SQFCWB4",
        )

    def test_youtube_embed_link_bad(self):
        self.assertEqual(
            books_extras.youtube_embed_link("https://hello.world"),
            "https://www.youtube.com/embed/",
        )
        self.assertEqual(
            books_extras.youtube_embed_link("abracadabra"),
            "https://www.youtube.com/embed/",
        )
        self.assertEqual(
            books_extras.youtube_embed_link("https://www.youtube.com/watch?id=123"),
            "https://www.youtube.com/embed/",
        )
