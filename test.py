import os
import unittest

from flask import Flask

os.environ["TEST"] = "true"

from app import app
from app import db
from models import Recipe
from models import Ingredient
from models import Menu

class RecipeTestCase(unittest.TestCase):
    """
    This class tests all recipe-api endpoints

    It uses a local ad-hoc sqlite database which
    is re-created for each test case. Also, it mocks
    the authentication functionality, so that the
    tests are independent of Auth0.
    """

    def setUp(self):
        """
        Set everything up and initialize database
        and application.
        """
        self.app = app
        self.db = db
        with self.app.app_context():
            self.db.create_all()
        self.client = self.app.test_client

    def tearDown(self):
        """
        Clean up by closing database and removing file
        """
        with self.app.app_context():
            self.db.session.close()
        os.remove(os.path.join(self.app.instance_path, "test-database.db"))

    def test_get_recipe_list_empty(self):
        res = self.client().get("/recipe")
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["recipes"], [])

    def test_get_recipe_list_empty_page_error(self):
        res = self.client().get("/recipe?page=2")
        data = res.get_json()

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["success"], False)

    def test_get_recipe_list_one_recipe(self):
        recipe = Recipe(
            name="Test Recipe",
            username="test@example.com",
            servings=4,
            ingredients=[
                Ingredient(name="gramms of spaghetti", amount=600),
                Ingredient(name="liters of water", amount=1),
                Ingredient(name="pinches of salt", amount=3),
            ],
            preparation=(
                "1. cook water, 2. add salt, 3. add spaghetti"
                "and cook until al dente, 4. drain water, 5. serve"
            )
        )
        with self.app.app_context():
            self.db.session.add(recipe)
            self.db.session.commit()

        res = self.client().get("/recipe")
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(len(data["recipes"]), 1)


if __name__ == "__main__":
    unittest.main()
