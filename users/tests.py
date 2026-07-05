from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import serializers
from rest_framework import status
from rest_framework.test import APIClient

from users.serializers import UserSerializer


class UserApiBlackBoxTests(TestCase):
	"""Pruebas de caja negra: validan comportamiento observable de la API."""

	def setUp(self):
		self.client = APIClient()
		self.collection_url = reverse("user-collection")

	def test_get_collection_returns_users_list(self):
		User.objects.create_user(
			username="alice",
			email="alice@example.com",
			first_name="Alice",
			last_name="Doe",
			password="Secret123!",
		)

		response = self.client.get(self.collection_url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]["username"], "alice")
		self.assertNotIn("password", response.data[0])

	def test_post_collection_creates_user(self):
		payload = {
			"username": "bob",
			"email": "bob@example.com",
			"first_name": "Bob",
			"last_name": "Smith",
			"password": "Secret123!",
		}

		response = self.client.post(self.collection_url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(User.objects.count(), 1)
		self.assertNotIn("password", response.data)
		self.assertEqual(response.data["email"], payload["email"])

	def test_post_collection_invalid_payload_returns_400(self):
		payload = {
			"username": "bob",
			"email": "invalid-email",
			"first_name": "",
			"last_name": "",
			"password": "Secret123!",
		}

		response = self.client.post(self.collection_url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("email", response.data)

	def test_get_element_not_found_returns_404(self):
		detail_url = reverse("user-element", kwargs={"pk": 999})

		response = self.client.get(detail_url)

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
		self.assertEqual(response.data["error"], "Usuario con ID 999 no encontrado.")

	def test_put_element_updates_user(self):
		user = User.objects.create_user(
			username="charlie",
			email="charlie@example.com",
			first_name="Charlie",
			last_name="Brown",
			password="Secret123!",
		)
		detail_url = reverse("user-element", kwargs={"pk": user.id})
		payload = {
			"username": "charlie-updated",
			"email": "charlie-updated@example.com",
			"first_name": "Charles",
			"last_name": "Brown",
			"password": "NewSecret123!",
		}

		response = self.client.put(detail_url, payload, format="json")
		user.refresh_from_db()

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(user.username, "charlie-updated")
		self.assertTrue(user.check_password("NewSecret123!"))

	def test_delete_element_removes_user(self):
		user = User.objects.create_user(
			username="to-delete",
			email="delete@example.com",
			first_name="To",
			last_name="Delete",
			password="Secret123!",
		)
		detail_url = reverse("user-element", kwargs={"pk": user.id})

		response = self.client.delete(detail_url)

		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
		self.assertFalse(User.objects.filter(id=user.id).exists())


class UserApiGrayBoxTests(TestCase):
	"""Pruebas de caja gris: combinan contrato API con conocimiento parcial de reglas internas."""

	def setUp(self):
		self.client = APIClient()
		self.collection_url = reverse("user-collection")

	def test_post_duplicate_email_returns_custom_validation_error(self):
		User.objects.create_user(
			username="existing",
			email="existing@example.com",
			first_name="Existing",
			last_name="User",
			password="Secret123!",
		)
		payload = {
			"username": "new-user",
			"email": "existing@example.com",
			"first_name": "New",
			"last_name": "User",
			"password": "Secret123!",
		}

		response = self.client.post(self.collection_url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("email", response.data)
		self.assertIn("Este correo electrónico ya está registrado.", response.data["email"][0])

	def test_put_same_email_on_same_user_is_allowed(self):
		user = User.objects.create_user(
			username="same-email",
			email="same@example.com",
			first_name="Same",
			last_name="Email",
			password="Secret123!",
		)
		detail_url = reverse("user-element", kwargs={"pk": user.id})
		payload = {
			"username": "same-email-updated",
			"email": "same@example.com",
			"first_name": "Same",
			"last_name": "Email",
			"password": "Secret123!",
		}

		response = self.client.put(detail_url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_put_email_used_by_other_user_returns_400(self):
		User.objects.create_user(
			username="owner",
			email="owner@example.com",
			first_name="Owner",
			last_name="User",
			password="Secret123!",
		)
		other = User.objects.create_user(
			username="other",
			email="other@example.com",
			first_name="Other",
			last_name="User",
			password="Secret123!",
		)
		detail_url = reverse("user-element", kwargs={"pk": other.id})
		payload = {
			"username": "other",
			"email": "owner@example.com",
			"first_name": "Other",
			"last_name": "User",
			"password": "Secret123!",
		}

		response = self.client.put(detail_url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("email", response.data)


class UserApiWhiteBoxTests(TestCase):
	"""Pruebas de caja blanca: ejercitan ramas y métodos internos de serializer y vista."""

	def setUp(self):
		self.client = APIClient()

	def test_serializer_create_hashes_password(self):
		serializer = UserSerializer(
			data={
				"username": "serializer-create",
				"email": "serializer-create@example.com",
				"first_name": "Serializer",
				"last_name": "Create",
				"password": "Secret123!",
			}
		)

		self.assertTrue(serializer.is_valid(), serializer.errors)
		user = serializer.save()

		self.assertNotEqual(user.password, "Secret123!")
		self.assertTrue(user.check_password("Secret123!"))

	def test_serializer_update_without_password_keeps_existing_hash(self):
		user = User.objects.create_user(
			username="serializer-update",
			email="serializer-update@example.com",
			first_name="Serializer",
			last_name="Update",
			password="OldSecret123!",
		)
		original_hash = user.password
		serializer = UserSerializer(
			user,
			data={
				"username": "serializer-update-2",
				"email": "serializer-update@example.com",
				"first_name": "Serializer",
				"last_name": "Update",
			},
			partial=True,
			context={"user_id": user.id},
		)

		self.assertTrue(serializer.is_valid(), serializer.errors)
		updated_user = serializer.save()

		self.assertEqual(updated_user.password, original_hash)
		self.assertTrue(updated_user.check_password("OldSecret123!"))

	def test_serializer_validate_email_rejects_duplicate_without_context(self):
		User.objects.create_user(
			username="one",
			email="dup@example.com",
			first_name="One",
			last_name="User",
			password="Secret123!",
		)
		serializer = UserSerializer()

		with self.assertRaisesMessage(
			serializers.ValidationError,
			"Este correo electrónico ya está registrado.",
		):
			serializer.validate_email("dup@example.com")

	def test_delete_returns_500_when_model_delete_raises_exception(self):
		user = User.objects.create_user(
			username="delete-error",
			email="delete-error@example.com",
			first_name="Delete",
			last_name="Error",
			password="Secret123!",
		)
		detail_url = reverse("user-element", kwargs={"pk": user.id})

		with patch("django.contrib.auth.models.User.delete", side_effect=Exception("db error")):
			response = self.client.delete(detail_url)

		self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
		self.assertEqual(
			response.data["error"],
			"No se pudo eliminar el usuario debido a un error del servidor.",
		)
