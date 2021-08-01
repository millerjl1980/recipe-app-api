from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTests(TestCase):
    """Test the public available Ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to access the endpoint"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test the private Ingredients API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@test.com',
            password='password12345'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingrediants_list(self):
        """Test retrieving a list of ingrediants"""
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Grapes')
        res = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_limited_to_user(self):
        """Test that only ingredients for the auth user are returned"""
        user2 = get_user_model().objects.create_user(
            email='otheruser@test.com',
            password='otherpassword1'
        )
        Ingredient.objects.create(user=user2, name='Kale')
        ingredient = Ingredient.objects.create(user=self.user, name='Grapes')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        """Creating an ingredient was successful"""
        payload = {'name': 'Cabbage'}
        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()
        self.assertTrue(exists)

    def test_ingredient_invalid(self):
        """Test that create and invaild ingredient fails"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipes(self):
        """Test filtering ingredient by those assigned to recipes"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Apples')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Turkey')
        recipe = Recipe.objects.create(
            title='Apple Crumble',
            time_minutes=10,
            price=5.00,
            user=self.user
        )
        recipe.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_ingredients_assigned_unique(self):
        """Test filtering ingredients by assigned returns unique items"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Eggs')
        Ingredient.objects.create(user=self.user, name='Cheese')
        recipe1 = Recipe.objects.create(
            title='Eggs Benedict',
            time_minutes=10,
            price=5.00,
            user=self.user
        )
        recipe1.ingredients.add(ingredient1)

        recipe2 = Recipe.objects.create(
            title='Eggs on toast',
            time_minutes=10,
            price=5.00,
            user=self.user
        )
        recipe2.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)
