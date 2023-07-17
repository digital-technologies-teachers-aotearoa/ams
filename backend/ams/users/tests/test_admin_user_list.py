from django.contrib.auth.models import User
from django.test import TestCase


class AdminUserListTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testuser", is_superuser=True)
        self.user.first_name = "John"
        self.user.last_name = "Smith"
        self.user.email = "user@example.com"
        self.user.save()

    def test_should_not_allow_access_to_non_admin_user(self) -> None:
        # Given
        self.user.is_superuser = False
        self.user.save()

        self.client.force_login(self.user)

        # When
        response = self.client.get("/users/list/")

        # Then
        self.assertEqual(403, response.status_code)

    def test_should_use_expected_templates(self) -> None:
        # Given
        self.client.force_login(self.user)

        # When
        response = self.client.get("/users/list/")

        # Then
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "admin_user_list.html")
        self.assertTemplateUsed(response, "admin_user_actions.html")

    def test_should_show_expected_columns(self) -> None:
        # Given
        self.client.force_login(self.user)

        # When
        response = self.client.get("/users/list/")

        # Then
        self.assertEqual(200, response.status_code)

        expected_columns = ["full_name", "email", "actions"]
        columns = [column.name for column in response.context["table"].columns]
        self.assertListEqual(expected_columns, columns)

    def test_should_show_expected_headings(self) -> None:
        # Given
        self.client.force_login(self.user)

        # When
        response = self.client.get("/users/list/")

        # Then
        self.assertEqual(200, response.status_code)

        expected_columns = ["Full Name", "Email", "Actions"]
        columns = [column.header for column in response.context["table"].columns]
        self.assertListEqual(expected_columns, columns)

    def test_should_show_expected_rows(self) -> None:
        # Given
        self.client.force_login(self.user)

        # When
        response = self.client.get("/users/list/")

        # Then
        self.assertEqual(200, response.status_code)

        rows = []
        for row in response.context["table"].rows:
            rows.append([cell for cell in row.cells])

        expected_rows = [[f"{self.user.first_name} {self.user.last_name}", self.user.email, ""]]

        self.assertListEqual(expected_rows, rows)
