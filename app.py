import logging
import os

from dotenv import load_dotenv
from flask import Flask
from flask import abort
from flask import g
from flask import jsonify
from flask import request
from flask import render_template
from flask import url_for
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

from auth import requires_auth
from auth import has_permission
from auth import AUTH0_DOMAIN
from auth import API_AUDIENCE

load_dotenv()

PAGE_SIZE = 10

app = Flask(__name__)
db = setup_db(app)
setup_error_handlers(app)
CORS(app)
Migrate(app, db)


def get_page():
    """
    Returns the page number and start and end indices.
    """
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    return page, start, end


def get_total_pages(total_items):
    """
    Returns the total number of pages.
    """
    return (total_items + PAGE_SIZE - 1) // PAGE_SIZE


def check_page(start, total_items):
    """
    Check whether the requested page is out of bounds.
    """
    if total_items == 0:
        if start > 0:
            err_bad_request("Page set beyond end of list")
    else:
        if start >= total_items:
            err_bad_request("Page set beyond end of list")


@app.route("/")
def get_index_infos():
    """
    The index route returns just a short informational text.

    This endpoint is public, thus does not require authentication.
    """
    return "This is the base URL of the recipe service API."


@app.route("/recipe")
def get_recipe_list():
    """
    Returns the paged list of recipes.

    This endpoint is public, thus does not require authentication.
    """
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


@app.route("/recipe/<int:recipe_id>")
def get_recipe(recipe_id):
    """
    Returns a specific recipe given by its recipe_id.

    This endpoint is public, thus does not require authentication.
    """
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


@app.route("/recipe", methods=("POST",))
@requires_auth("add:recipe")
def add_recipe():
    """
    Adds a recipe to the database.
    """
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
            username=g.username,
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


@app.route("/recipe/<int:recipe_id>", methods=("PATCH",))
@requires_auth("update:recipe")
def update_recipe(recipe_id):
    """
    Updates an existing recipe identified by its recipe_id.

    This only works if the same user created the recipe, or
    if the current user has administrative privileges.
    """
    data = request.get_json()
    try:
        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            err_not_found(f"Recipe {recipe_id} not found")
        if recipe.username != g.username and not has_permission("update:any-recipe"):
            err_forbidden("Cannot update recipes of other users")
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


@app.route("/recipe/<int:recipe_id>", methods=("DELETE",))
@requires_auth("delete:recipe")
def delete_recipe(recipe_id):
    """
    Deletes a recipe given by its recipe_id.

    This only works if the same user created the recipe,
    or if the current user has administrative privileges.
    """
    try:
        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            err_not_found(f"Recipe {recipe_id} not found")
        if recipe.menus:
            err_forbidden(
                f"Cannot delete recipe {recipe_id} "
                "because it is used in menus"
            )
        if recipe.username != g.username and not has_permission("delete:any-recipe"):
            err_forbidden("Cannot delete recipes of other users")
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


@app.route("/menu")
def get_menu_list():
    """
    Returns the paged list of menus.

    This endpoint is public, thus does not require authentication.
    """
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


@app.route("/menu/<int:menu_id>")
def get_menu(menu_id):
    """
    Return a specific menu given by the menu_id.

    This endpoint is public, thus does not require authentication.
    """
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


@app.route("/menu", methods=("POST",))
@requires_auth("add:menu")
def add_menu():
    """
    Adds a new menu to the database.
    """
    data = request.get_json()
    try:
        if "name" not in data:
            err_bad_request("Field 'name' is missing")
        if "dishes" not in data:
            err_bad_request("Field 'dishes' is missing")
        menu = Menu(
            name=data["name"],
            username=g.username,
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


@app.route("/menu/<int:menu_id>", methods=("PATCH",))
@requires_auth("update:menu")
def update_menu(menu_id):
    """
    Updates a menu identified by its menu_id.

    This only works if the same user created the menu
    or if the current user has administrative privileges.
    """
    data = request.get_json()
    try:
        menu = db.session.get(Menu, menu_id)
        if not menu:
            err_not_found(f"Menu {menu_id} not found")
        if menu.username != g.username and not has_permission("update:any-menu"):
            err_forbidden("Cannot update menus of other users")
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


@app.route("/menu/<int:menu_id>", methods=("DELETE",))
@requires_auth("delete:menu")
def delete_menu(menu_id):
    """
    Deletes a menu identified by its menu_id.

    This only works if the same user created the menu
    or if the current user has administrative privileges.
    """
    try:
        menu = db.session.get(Menu, menu_id)
        if not menu:
            err_not_found(f"Menu {menu_id} not found")
        if menu.username != g.username and not has_permission("delete:any-menu"):
            err_forbidden("Cannot delete menus of other users")
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


# The following two routes are not formally part of the API.
# Instead, they provide a very simple GUI for logging in
# using Auth0 and retrieving the JWT token required for accessing
# the API.

@app.route("/connect")
def ui_connect():
    client_id = os.environ["AUTH0_CLIENT_ID"]
    redirect_url = url_for('ui_token', _external=True)
    redirect_url = redirect_url.replace("localhost", "127.0.0.1")
    authorize_url = (
        f"https://{AUTH0_DOMAIN}/authorize"
        f"?audience={API_AUDIENCE}"
        f"&response_type=token"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_url}"
    )
    logout_url = f"https://{AUTH0_DOMAIN}/logout"
    return render_template(
        "connect.html",
        auth0_authorize_url=authorize_url,
        auth0_logout_url=logout_url,
    )


@app.route("/token")
def ui_token():
    return render_template("token.html")


if __name__ == '__main__':
    app.run()
