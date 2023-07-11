from django.test import TestCase


class PageTests(TestCase):
    def test_should_show_homepage(self) -> None:
        # Given
        response = self.client.get("/")

        # Then
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "base/home_page.html")

    def test_should_show_membership_page(self) -> None:
        # Given
        response = self.client.get("/membership/")

        # Then
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "base/membership_page.html")
