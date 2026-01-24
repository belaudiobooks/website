from selenium.webdriver.common.by import By

from partners.tests.webdriver_test_case import WebdriverTestCase


class DashboardTest(WebdriverTestCase):
    def test_unauthenticated_user_redirected_to_login(self):
        """Unauthenticated users should be redirected to login page."""
        self.driver.get(f"{self.live_server_url}/partners/")
        self.assertIn("/partners/login/", self.driver.current_url)
        self.assertIn("Уваход для партнёраў", self.driver.page_source)

    def test_login_and_view_dashboard(self):
        """Partner user can login and see the dashboard."""
        self.login()

        # Should be redirected to dashboard
        self.assertEqual(f"{self.live_server_url}/partners/", self.driver.current_url)
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
