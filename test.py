import os
import unittest

from flask import Flask

os.environ["TEST"] = "true"

from app import app
from app import db
from models import Recipe
from models import Ingredient
from models import Menu


def create_recipe(spec):
    lines = spec.strip().splitlines()
    recipe = Recipe(
        name=lines[0].strip(),
        username=lines[1].strip(),
        servings=int(lines[2].strip().split(" ")[0]),
        preparation="",
    )
    in_ingredients = True
    for line in lines[4:]:
        line = line.strip()
        if in_ingredients and line == "":
            in_ingredients = False
        if in_ingredients:
            recipe.ingredients.append(
                Ingredient(
                    amount=float(line.split(" ", 1)[0]),
                    name=line.split(" ", 1)[1],
                )
            )
        else:
            recipe.preparation += line + "\n"
    return recipe


def create_simple_salad():
    return create_recipe("""
    Simple Salad
    test@example.com
    4 servings

    1 lettuce
    2 teaspoons of vinegar
    3 teaspoons of sun flower oil
    1 salt and pepper

    Wash and cut lettuce

    Mix vinegar, oil, salt and pepper into
    a fine vinaigrette

    Mix lettuce and vinaigrette

    Serve
    """)


def create_spaghetti_with_tomato_sauce():
    return create_recipe("""
    Spaghetti with tomato sauce
    test@example.com
    4 servings

    500 gramms of spaghetti
    1 litre salted water
    5 tomatoes
    1 branch of basil
    1 small onion
    1 spoon of olive oil
    1 salt and pepper

    Finely slice onion and cook in olive oil
    Chop tomatoes into medium pieces and add
    Roughly chop basil and add
    Season with salt and pepper
    Cook on low grade
    Boil the water, add salt and spaghetti
    Cook until they are al dente
    Remove spaghetti from water
    Mix with the sauce and serve
    """)


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

    def test_get_recipe_list_error_page_bounds(self):
        res = self.client().get("/recipe?page=2")
        data = res.get_json()

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["success"], False)

    def test_get_recipe_list_one_recipe(self):
        recipe = create_simple_salad()
        with self.app.app_context():
            self.db.session.add(recipe)
            self.db.session.commit()

        res = self.client().get("/recipe")
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(len(data["recipes"]), 1)

    def test_get_recipe_list_two_recipes(self):
        with self.app.app_context():
            self.db.session.add(create_simple_salad())
            self.db.session.add(create_spaghetti_with_tomato_sauce())
            self.db.session.commit()

        res = self.client().get("/recipe")
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(len(data["recipes"]), 2)

    def test_get_recipe(self):
        recipe = create_simple_salad()
        with self.app.app_context():
            self.db.session.add(recipe)
            self.db.session.flush()
            recipe_id = recipe.id
            self.db.session.commit()

        res = self.client().get(f"/recipe/{recipe_id}")
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["recipe"]["name"], "Simple Salad")

    def test_get_recipe_error_not_found(self):
        res = self.client().get(f"/recipe/1")
        data = res.get_json()

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)

    def test_add_recipe(self):
        recipe = {
            "name": "Test",
            "servings": 1,
            "ingredients": [
                {"name": "slice of bread", "amount": 1},
                {"name": "bit of butter", "amount": 1},
            ],
            "preparation": "Spread butter on slice of bread. Serve",
        }
        res = self.client().post("/recipe", json=recipe)
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)

        recipe_id = data["id"]
        res = self.client().get(f"/recipe/{recipe_id}")
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["recipe"]["name"], "Test")


    def test_add_recipe_error_missing_fields(self):
        recipe = {
            "name": "Test",
        }
        res = self.client().post(f"/recipe", json=recipe)
        data = res.get_json()

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["success"], False)

    def test_update_recipe(self):
        recipe = create_simple_salad()
        with self.app.app_context():
            self.db.session.add(recipe)
            self.db.session.flush()
            recipe_id = recipe.id
            self.db.session.commit()

        recipe = {
            "name": "Test Salad",
            "servings": 1,
        }
        res = self.client().patch(f"/recipe/{recipe_id}", json=recipe)
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["id"], recipe_id)

        res = self.client().get(f"/recipe/{recipe_id}")
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["recipe"]["name"], "Test Salad")
        self.assertEqual(data["recipe"]["servings"], 1)

    def test_update_recipe_error_not_found(self):
        recipe = {
            "name": "Test Salad",
            "servings": 1,
        }
        res = self.client().patch(f"/recipe/1", json=recipe)
        data = res.get_json()

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)

    def test_delete_recipe(self):
        recipe = create_simple_salad()
        with self.app.app_context():
            self.db.session.add(recipe)
            self.db.session.flush()
            recipe_id = recipe.id
            self.db.session.commit()

        res = self.client().delete(f"/recipe/{recipe_id}")
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["id"], recipe_id)

        res = self.client().get(f"/recipe/{recipe_id}")
        data = res.get_json()

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)

    def test_delete_recipe_error_not_found(self):
        res = self.client().delete(f"/recipe/1")
        data = res.get_json()

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)

    def test_delete_recipe_error_included_in_menu(self):
        recipe = create_simple_salad()
        menu = Menu(
            name="Testmenu",
            username="test@example.com",
            dishes=[recipe],
        )
        with self.app.app_context():
            self.db.session.add(recipe)
            self.db.session.add(menu)
            self.db.session.flush()
            recipe_id = recipe.id
            menu_id = menu.id
            self.db.session.commit()

        res = self.client().delete(f"/recipe/{recipe_id}")
        data = res.get_json()

        self.assertEqual(res.status_code, 403)
        self.assertEqual(data["success"], False)

    def test_get_menu_list_empty(self):
        res = self.client().get("/menu")
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["menus"], [])

    def test_get_menu_list_error_page_bounds(self):
        res = self.client().get("/menu?page=2")
        data = res.get_json()

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["success"], False)

    def test_get_menu_list_one(self):
        recipe = create_simple_salad()
        menu = Menu(
            name="Testmenu",
            username="test@example.com",
            dishes=[recipe],
        )
        with self.app.app_context():
            self.db.session.add(recipe)
            self.db.session.add(menu)
            self.db.session.flush()
            recipe_id = recipe.id
            menu_id = menu.id
            self.db.session.commit()

        res = self.client().get("/menu")
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(len(data["menus"]), 1)

    def test_get_menu(self):
        recipe = create_simple_salad()
        menu = Menu(
            name="Testmenu",
            username="test@example.com",
            dishes=[recipe],
        )
        with self.app.app_context():
            self.db.session.add(recipe)
            self.db.session.add(menu)
            self.db.session.flush()
            recipe_id = recipe.id
            menu_id = menu.id
            self.db.session.commit()

        res = self.client().get(f"/menu/{menu_id}")
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["menu"]["name"], "Testmenu")

    def test_get_menu_error_not_found(self):
        res = self.client().get(f"/menu/1")
        data = res.get_json()

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)

    def test_add_menu(self):
        recipe = create_simple_salad()
        with self.app.app_context():
            self.db.session.add(recipe)
            self.db.session.flush()
            recipe_id = recipe.id
            self.db.session.commit()

        menu = {
            "name": "Testmenu",
            "dishes": [{"recipe_id": recipe_id}],
        }
        res = self.client().post("/menu", json=menu)
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)

        menu_id = data["id"]
        res = self.client().get(f"/menu/{menu_id}")
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["menu"]["name"], "Testmenu")

    def test_add_menu_error_missing_name(self):
        recipe = create_simple_salad()
        with self.app.app_context():
            self.db.session.add(recipe)
            self.db.session.flush()
            recipe_id = recipe.id
            self.db.session.commit()

        menu = {
            "dishes": [{"recipe_id": recipe_id}],
        }
        res = self.client().post(f"/menu", json=menu)
        data = res.get_json()

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["success"], False)

    def test_update_menu(self):
        recipe = create_simple_salad()
        menu = Menu(
            name="Testmenu",
            username="test@example.com",
            dishes=[recipe],
        )
        with self.app.app_context():
            self.db.session.add(recipe)
            self.db.session.add(menu)
            self.db.session.flush()
            recipe_id = recipe.id
            menu_id = menu.id
            self.db.session.commit()

        menu = {
            "name": "Changed",
        }
        res = self.client().patch(f"/menu/{menu_id}", json=menu)
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["id"], menu_id)

        res = self.client().get(f"/menu/{menu_id}")
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["menu"]["name"], "Changed")

    def test_update_menu_error_not_found(self):
        menu = {
            "name": "Changed",
        }
        res = self.client().patch("/menu/1", json=menu)
        data = res.get_json()

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)

    def test_delete_menu(self):
        recipe = create_simple_salad()
        menu = Menu(
            name="Testmenu",
            username="test@example.com",
            dishes=[recipe],
        )
        with self.app.app_context():
            self.db.session.add(recipe)
            self.db.session.add(menu)
            self.db.session.flush()
            recipe_id = recipe.id
            menu_id = menu.id
            self.db.session.commit()

        res = self.client().delete(f"/menu/{menu_id}")
        data = res.get_json()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["id"], menu_id)

        res = self.client().get(f"/menu/{menu_id}")
        data = res.get_json()

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)

    def test_delete_menu_error_not_found(self):
        res = self.client().delete(f"/menu/1")
        data = res.get_json()

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)


if __name__ == "__main__":
    unittest.main()
