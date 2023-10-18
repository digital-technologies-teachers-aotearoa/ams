import os
import random
import tempfile
from filecmp import cmp

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from PIL import Image


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class UpdateUserProfileImageTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testuser", is_staff=False)

        self.temp_image_dir = tempfile.gettempdir()

        self.image = Image.new("RGB", (512, 512))
        self.image_path = f"{self.temp_image_dir}/test_image.png"
        self.image.save(self.image_path, "PNG")

        self.assertTrue(os.path.exists(self.image_path))

        self.url = "/users/current/"
        self.client.force_login(self.user)

    def test_should_update_profile_image_with_valid_image(self) -> None:
        # When
        image_file_handle = open(self.image_path, "rb")
        response = self.client.post(
            self.url, {"action": "upload_profile_image", "profile_image_file": image_file_handle}
        )

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(self.url, response.url)

        self.user.refresh_from_db()

        uploaded_image_path = f"{settings.MEDIA_ROOT}/{self.user.profile.image}"
        self.assertTrue(os.path.exists(uploaded_image_path))
        self.assertTrue(cmp(self.image_path, uploaded_image_path, shallow=False))

    def test_admin_can_update_users_image(self) -> None:
        # When
        admin_user = User.objects.create_user(username="testadminuser", is_staff=True)
        self.client.force_login(admin_user)

        image_file_handle = open(self.image_path, "rb")
        user_view_url = f"/users/view/{self.user.pk}/"

        response = self.client.post(
            user_view_url, {"action": "upload_profile_image", "profile_image_file": image_file_handle}
        )

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(user_view_url, response.url)

        self.user.refresh_from_db()

        uploaded_image_path = f"{settings.MEDIA_ROOT}/{self.user.profile.image}"
        self.assertTrue(os.path.exists(uploaded_image_path))
        self.assertTrue(cmp(self.image_path, uploaded_image_path, shallow=False))

    def test_should_update_profile_image_with_valid_gif(self) -> None:
        # When
        image = Image.new("RGB", (512, 512))
        image_path = f"{self.temp_image_dir}/test_image.gif"
        image.save(image_path, "GIF")

        image_file_handle = open(image_path, "rb")
        response = self.client.post(
            self.url, {"action": "upload_profile_image", "profile_image_file": image_file_handle}
        )

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(self.url, response.url)

    def test_should_update_profile_image_with_valid_jpeg(self) -> None:
        # When
        image = Image.new("RGB", (512, 512))
        image_path = f"{self.temp_image_dir}/test_image.jpg"
        image.save(image_path, "JPEG")

        image_file_handle = open(image_path, "rb")
        response = self.client.post(
            self.url, {"action": "upload_profile_image", "profile_image_file": image_file_handle}
        )

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(self.url, response.url)

    def test_should_show_expected_error_for_invalid_image(self) -> None:
        # When
        response = self.client.post(self.url, {"action": "upload_profile_image", "profile_image_file": "invalid image"})

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"{self.url}?invalid_profile_image=true", response.url)

        response = self.client.get(response.url)

        expected_messages = [
            {"value": "Your profile image must be valid JPG, PNG or GIF not exceeding 1MB in size.", "type": "error"}
        ]
        self.assertListEqual(expected_messages, response.context["show_messages"])

    def test_should_show_error_for_over_sized_invalid_image(self) -> None:
        # When
        # Create an large random image which wont compress well
        image = Image.new("RGB", (768, 768))
        pixels = image.load()
        for x in range(image.size[0]):
            for y in range(image.size[1]):
                pixels[x, y] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        image_path = f"{self.temp_image_dir}/random_test_image.png"
        image.save(image_path, "PNG")

        file_size = os.path.getsize(image_path)
        self.assertGreater(file_size, 1048576)

        image_file_handle = open(image_path, "rb")
        response = self.client.post(
            self.url, {"action": "upload_profile_image", "profile_image_file": image_file_handle}
        )

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"{self.url}?invalid_profile_image=true", response.url)
