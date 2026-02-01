from decimal import Decimal

from selenium.webdriver.common.by import By

from partners.models import Agreement, Partner
from partners.tests.webdriver_test_case import WebdriverTestCase


class DashboardTest(WebdriverTestCase):
    def test_unauthenticated_user_redirected_to_login(self):
        """Unauthenticated users should be redirected to login page."""
        self.driver.get(f"{self.live_server_url}/partners/")
        self.assertIn("/partners/login/", self.driver.current_url)
        self.assertIn("Уваход для партнёраў", self.driver.page_source)

    def test_user_from_different_partner_gets_forbidden(self):
        """User from a different partner should get 403."""
        other_partner = Partner.objects.create(name="Other Partner")
        self.login()
        self.driver.get(f"{self.live_server_url}/partners/{other_partner.id}/")
        # HttpResponseForbidden returns empty body
        self.assertNotIn("Партнёрская панэль", self.driver.page_source)

    def test_login_and_view_dashboard(self):
        """Partner user can login and see the dashboard."""
        self.login()

        # Should be redirected to partner's dashboard
        self.assertEqual(
            f"{self.live_server_url}/partners/{self.partner.id}/",
            self.driver.current_url,
        )
        self.assertIn("Партнёрская панэль", self.driver.page_source)

    def test_invalid_login_shows_error(self):
        """Invalid credentials should show error message."""
        self.driver.get(f"{self.live_server_url}/partners/login/")

        # Fill in wrong credentials
        email_input = self.driver.find_element(By.ID, "email")
        password_input = self.driver.find_element(By.ID, "password")
        email_input.send_keys("wrong@email.com")
        password_input.send_keys("wrongpassword")

        # Submit form using form submit to avoid navbar button conflicts
        form = self.driver.find_element(By.CSS_SELECTOR, "form[action*='login']")
        form.submit()

        # Should stay on login page with error
        self.assertIn("/partners/login/", self.driver.current_url)
        self.assertIn("Няправільны емэйл або пароль", self.driver.page_source)

    def test_dashboard_shows_agreements_count(self):
        """Dashboard should display correct count of books and narrations."""
        fake = self.books_fake_data
        book1 = fake.create_book_with_single_narration(
            title="Book 1",
            authors=[fake.person_ales],
            narrators=[fake.person_bela],
        )
        book2 = fake.create_book_with_single_narration(
            title="Book 2",
            authors=[fake.person_viktar],
            narrators=[fake.person_volha],
        )

        # Create agreement with 1 narration and 1 book = 2 total
        agreement = Agreement.objects.create(
            partner=self.partner, royalty_percent=Decimal("10.00")
        )
        agreement.narrations.add(book1.narrations.first())
        agreement.books.add(book2)

        self.login()

        count = self.driver.find_element(
            By.CSS_SELECTOR, "[data-test-id='agreements-count']"
        )
        self.assertEqual("2", count.text)

    def test_clicking_agreements_card_redirects_to_agreements(self):
        """Clicking on agreements card should redirect to agreements page."""
        self.login()

        card = self.driver.find_element(
            By.CSS_SELECTOR, "[data-test-id='agreements-card']"
        )
        card.click()

        self.assertEqual(
            f"{self.live_server_url}/partners/{self.partner.id}/agreements/",
            self.driver.current_url,
        )

    def test_login_by_uuid(self):
        """Partner user can login via UUID link."""
        self.driver.get(
            f"{self.live_server_url}/partners/login/{self.user.login_uuid}/"
        )

        # Should be redirected to partner's dashboard
        self.assertEqual(
            f"{self.live_server_url}/partners/{self.partner.id}/",
            self.driver.current_url,
        )
        self.assertIn("Партнёрская панэль", self.driver.page_source)
