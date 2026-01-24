from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from books.tests.fake_data import FakeData
from partners.models import Agreement, Partner, PartnerUser


@override_settings(DEBUG=True)
class WebdriverTestCase(StaticLiveServerTestCase):
    """Base class for all webdriver tests in partners app."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless")
        cls.driver = webdriver.Chrome(
            options=options, service=ChromeService(ChromeDriverManager().install())
        )
        cls.driver.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.driver.delete_all_cookies()
        self.books_fake_data = FakeData()
        self.partner = Partner.objects.create(name="Test Partner")
        self.user = PartnerUser.objects.create_user(
            email="test@partner.com", password="testpass123", partner=self.partner
        )

    def tearDown(self):
        self.books_fake_data.cleanup()
        for agreement in Agreement.objects.all():
            if agreement.agreement_file:
                agreement.agreement_file.delete()
        super().tearDown()

    def login(self):
        """Log in the test user via the login form."""
        self.driver.get(f"{self.live_server_url}/partners/login/")
        email_input = self.driver.find_element(By.ID, "email")
        password_input = self.driver.find_element(By.ID, "password")
        email_input.send_keys(self.user.email)
        password_input.send_keys("testpass123")
        form = self.driver.find_element(By.CSS_SELECTOR, "form[action*='login']")
        form.submit()
