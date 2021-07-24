from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


def create_user(**params):
    """helper function to setup users in tests"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """tests the users API (public/un-authenticated)"""

    def setup(self):
        self.client = APIClient()

    def test_create_valid_user_successful(self):
        """test creating user with valid payload is successful"""
        payload = {
            'email': 'test@email.com',
            'password': 'password1234',
            'name': 'Test name',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """tests createing user that already exists fails"""
        payload = {
            'email': 'test@email.com',
            'password': 'password1234',
            'name': 'Jester Tester',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """test password must be more than 10 characters"""
        payload = {
            'email': 'test@email.com',
            'password': 'pw',
            'name': 'Jester Tester',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """test that a token is created for user"""
        payload = {
            'email': 'test@email.com',
            'password': 'password1234',
            'name': 'Jester Tester'
        }
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """test that token not created for invalid credentials"""
        create_user(
            email='test@email.com',
            password="password1234",
            name='Jester Tester'
        )
        payload = {'email': 'test@email.com', 'password': 'wrongPassword'}
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """test that token is not created if user does not exist"""
        payload = {
            'email': 'test@email.com',
            'password': 'password1234',
            'name': 'Jester Tester'
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """test that email and password are required"""
        res = self.client.post(TOKEN_URL, {'email': 'one', 'password': ''})
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
