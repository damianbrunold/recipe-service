import logging
import os

from dotenv import load_dotenv
from flask import Flask
from flask import abort
from flask import jsonify
from flask import request
from flask_cors import CORS
from flask_migrate import Migrate
from werkzeug.exceptions import HTTPException

from error import setup_error_handlers
from error import success
from error import success2
from error import failure
from error import err_bad_request
from error import err_unauthorized
from error import err_forbidden
from error import err_not_found
from error import err_method_not_allowed
from error import err_unprocessable
from error import err_server_error

from models import setup_db
from models import Recipe
from models import Ingredient
from models import Menu

load_dotenv()

PAGE_SIZE = 10

app = Flask(__name__)
db = setup_db(app)
setup_error_handlers(app)
CORS(app)
Migrate(app, db)


def get_page():
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    return page, start, end


def get_total_pages(total_items):
    return (total_items + PAGE_SIZE - 1) // PAGE_SIZE


def check_page(start, total_items):
    if total_items == 0:
        if start > 0:
            err_bad_request("Page set beyond end of list")
    else:
        if start >= total_items:
            err_bad_request("Page set beyond end of list")


@app.route('/recipe')
def get_recipe_list():
    try:
        page, start, end = get_page()
        recipes = Recipe.query.order_by(Recipe.name).all()
        check_page(start, len(recipes))
        return jsonify({
            "success": True,
            "page": page,
            "total_pages": get_total_pages(len(recipes)),
            "recipes": [
                recipe.json_short()
                for recipe
                in recipes[start:end]
            ],
        })
    except HTTPException:
        raise
    except:
        msg = "Cannot get the recipe list"
        logging.exception(msg)
        err_server_error(msg)


@app.route('/recipe/<int:recipe_id>')
def get_recipe(recipe_id):
    try:
        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            err_not_found(f"Recipe {recipe_id} not found")
        return jsonify({
            "success": True,
            "recipe": recipe.json(),
        })
    except HTTPException:
        raise
    except:
        msg = f"Cannot get the recipe {recipe_id}"
        logging.exception(msg)
        err_server_error(msg)


@app.route('/recipe', methods=("POST",))
def add_recipe():
    data = request.get_json()
    try:
        if "name" not in data:
            err_bad_request("Field 'name' is missing")
        if "servings" not in data:
            err_bad_request("Field 'servings' is missing")
        if not isinstance(data["servings"], int):
            err_bad_request("Field 'servings' is not an integer")
        if "ingredients" not in data:
            err_bad_request("Field 'ingredients' is missing")
        recipe = Recipe(
            name=data["name"],
            username="test@example.com", # TODO take from authentication
            servings=data["servings"],
            preparation=data.get("preparation", "")
        )
        for idx, ingredient in enumerate(data["ingredients"]):
            if "amount" not in ingredient:
                err_bad_request(f"Field 'amount' is missing in ingredient {idx}")
            if "name" not in ingredient:
                err_bad_request(f"Field 'name' is missing in ingredient {idx}")
            if (
                not isinstance(ingredient["amount"], int)
                and not isinstance(ingredient["amount"], float)
            ):
                err_bad_request(f"Field 'amount' is not numerical in ingredient {idx}")
            new_ingredient = Ingredient(
                name=ingredient["name"],
                amount=ingredient["amount"],
            )
            recipe.ingredients.append(new_ingredient)            
        db.session.add(recipe)
        db.session.flush()
        recipe_id = recipe.id
        db.session.commit()
        return success2(
            "msg", f"Added recipe with id {recipe_id}",
            "id", recipe_id,
        ) 
    except HTTPException:
        raise
    except Exception:
        msg = "Cannot add new recipe"
        logging.exception(msg)
        err_server_error(msg)


@app.route('/recipe/<int:recipe_id>', methods=("PATCH",))
def update_recipe(recipe_id):
    data = request.get_json()
    try:
        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            err_not_found(f"Recipe {recipe_id} not found")
        if "name" in data:
            recipe.name = data["name"]
        if "servings" in data:
            if not isinstance(data["servings"], int):
                err_bad_request("Field 'servings' is not an integer")
            recipe.servings = data["servings"]
        if "ingredients" in data:
            new_ingredients = data["ingredients"]
            recipe.ingredients.clear()
            for idx, ingredient in enumerate(data["ingredients"]):
                if "amount" not in ingredient:
                    err_bad_request(f"Field 'amount' is missing in ingredient {idx}")
                if "name" not in ingredient:
                    err_bad_request(f"Field 'name' is missing in ingredient {idx}")
                if (
                    not isinstance(ingredient["amount"], int)
                    and not isinstance(ingredient["amount"], float)
                ):
                    err_bad_request(f"Field 'amount' is not numerical in ingredient {idx}")
                new_ingredient = Ingredient(
                    name=ingredient["name"],
                    amount=ingredient["amount"],
                )
                recipe.ingredients.append(new_ingredient)
        if "preparation" in data:
            recipe.preparation = data["preparation"]
        db.session.commit()
        return success2(
            "msg", f"Updated recipe with id {recipe_id}",
            "id", recipe_id,
        )
    except HTTPException:
        raise
    except Exception:
        msg = f"Cannot update recipe {recipe_id}"
        logging.exception(msg)
        err_server_error(msg)


@app.route('/recipe/<int:recipe_id>', methods=("DELETE",))
def delete_recipe(recipe_id):
    try:
        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            err_not_found(f"Recipe {recipe_id} not found")
        if recipe.menus:
            err_forbidden(
                f"Cannot delete recipe {recipe_id} "
                "because it is used in menus"
            )
        db.session.delete(recipe)
        db.session.commit()
        return success2(
            "msg", f"Recipe {recipe_id} deleted",
            "id", recipe_id,
        )
    except HTTPException:
        raise
    except Exception:
        msg = f"Cannot delete the recipe {recipe_id}"
        logging.exception(msg)
        err_server_error(msg)


@app.route('/menu')
def get_menu_list():
    try:
        page, start, end = get_page()
        menus = Menu.query.order_by(Menu.name).all()
        check_page(start, len(menus))
        return jsonify({
            "success": True,
            "page": page,
            "total_pages": get_total_pages(len(menus)),
            "menus": [
                menu.json_short()
                for menu
                in menus[start:end]
            ],
        })
    except HTTPException:
        raise
    except:
        msg = "Cannot get the menu list"
        logging.exception(msg)
        err_server_error(msg)


@app.route('/menu/<int:menu_id>')
def get_menu(menu_id):
    try:
        menu = db.session.get(Menu, menu_id)
        if not menu:
            err_not_found(f"Menu {menu_id} not found")
        return jsonify({
            "success": True,
            "menu": menu.json(),
        })
    except HTTPException:
        raise
    except:
        msg = f"Cannot get the menu {menu_id}"
        logging.exception(msg)
        err_server_error(msg)


@app.route('/menu', methods=("POST",))
def add_menu():
    data = request.get_json()
    try:
        if "name" not in data:
            err_bad_request("Field 'name' is missing")
        if "dishes" not in data:
            err_bad_request("Field 'dishes' is missing")
        menu = Menu(
            name=data["name"],
            username="test@example.com", # TODO take from authentication
        )
        for idx, dish in enumerate(data["dishes"]):
            if "recipe_id" not in dish:
                err_bad_request(f"Field 'recipe_id' is missing in dish {idx}")
            recipe_id = dish["recipe_id"]
            recipe = db.session.get(Recipe, recipe_id)
            if not recipe:
                err_bad_request(f"Recipe {recipe_id} in dish {idx} not found")
            menu.dishes.append(recipe)
        db.session.add(menu)
        db.session.flush()
        menu_id = menu.id
        db.session.commit()
        return success2(
            "msg", f"Added menu with id {menu_id}",
            "id", menu_id,
        )
    except HTTPException:
        raise
    except Exception:
        msg = "Cannot add new menu"
        logging.exception(msg)
        err_server_error(msg)


@app.route('/menu/<int:menu_id>', methods=("PATCH",))
def update_menu(menu_id):
    data = request.get_json()
    try:
        menu = db.session.get(Menu, menu_id)
        if not menu:
            err_not_found(f"Menu {menu_id} not found")
        if "name" in data:
            menu.name = data["name"]
        if "dishes" in data:
            menu.dishes.clear()
            for idx, dish in enumerate(data["dishes"]):
                if "recipe_id" not in dish:
                    err_bad_request(f"Field 'recipe_id' is missing in dish {idx}")
                recipe_id = dish["recipe_id"]
                recipe = db.session.get(Recipe, recipe_id)
                if not recipe:
                    err_bad_request(f"Recipe {recipe_id} in dish {idx} not found")
                menu.dishes.append(recipe)
        db.session.commit()
        return success2(
            "msg", f"Updated menu with id {menu_id}",
            "id", menu_id,
        )
    except HTTPException:
        raise
    except Exception:
        msg = f"Cannot update menu {menu_id}"
        logging.exception(msg)
        err_server_error(msg)


@app.route('/menu/<int:menu_id>', methods=("DELETE",))
def delete_menu(menu_id):
    try:
        menu = db.session.get(Menu, menu_id)
        if not menu:
            err_not_found(f"Menu {menu_id} not found")
        db.session.delete(menu)
        db.session.commit()
        return success2(
            "msg", f"Menu {menu_id} deleted",
            "id", menu_id,
        )
    except HTTPException:
        raise
    except Exception:
        msg = f"Cannot delete the menu {menu_id}"
        logging.exception(msg)
        err_server_error(msg)


if __name__ == '__main__':
    app.run()
