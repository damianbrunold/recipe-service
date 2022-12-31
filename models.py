import os

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


'''
setup_db(app)

binds a flask application and a SQLAlchemy service.

If test is True, then a local test database is used
'''
def setup_db(app):
    test = os.environ.get("TEST", "")
    if test == "true":
        dbfile = "test-database.db"
        path = os.path.join(app.instance_path, dbfile)
        if os.path.exists(path):
            os.remove(path)
        database_path = "sqlite:///" + dbfile
        app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    else:
        database_path = os.environ["DATABASE_URL"]
        if database_path.startswith("postgres://"):
            database_path = database_path.replace("postgres://", "postgresql://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)
    return db


'''
Recipe

A food recipe contains a list of ingredients and
preparation instructions.
'''
class Recipe(db.Model):  
    __tablename__ = 'recipe'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    servings = db.Column(db.Integer, nullable=False)
    preparation = db.Column(db.String())

    ingredients = db.relationship(
        "Ingredient",
        cascade="all, delete-orphan",
        backref="recipe"
    )

    def __repr__(self):
        return f"<Recipe {self.id}: {self.name} ({self.username})>"

    def json_short(self):
        return {
            "id": self.id,
            "name": self.name,
            "username": self.username,
        }

    def json(self):
        return {
            "id": self.id,
            "name": self.name,
            "username": self.username,
            "servings": self.servings,
            "ingredients": [
                ingredient.json()
                for ingredient
                in self.ingredients
            ],
            "preparation": self.preparation,
        }


'''
Ingredient

Models a single ingredient for a food recipe.
Since the amount is provided, it is possible to
increase/decrease the recipe amounts.
'''
class Ingredient(db.Model):
    __tablename__ = 'ingredient'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"))

    def __repr__(self):
        return f"<Ingredient {self.id}: {self.amount} {self.name}>"

    def json(self):
        return {
            "name": self.name,
            "amount": self.amount,
        }


'''
Association table for implementing n-m 
relationship between recipe and menu
(a menu contains n recipes, a recipe may
be used in m menus).
'''
menu_recipe_table = db.Table(
    "menu_recipe_table",
    db.Column('menu_id', db.Integer, db.ForeignKey('menu.id'), primary_key=True),
    db.Column('recipe_id', db.Integer, db.ForeignKey('recipe.id'), primary_key=True),
)


'''
Menu

A menu consists of a series of dishes/recipes.
'''
class Menu(db.Model):
    __tablename__ = 'menu'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    dishes = db.relationship(
        "Recipe", 
        secondary=menu_recipe_table,
        backref=db.backref('menus', lazy=True),
    )

    def __repr__(self):
        return f"<Menu {self.id}: {self.name} ({self.username})>"

    def json_short(self):
        return {
            "id": self.id,
            "name": self.name,
            "username": self.username,
        }

    def json(self):
        return {
            "id": self.id,
            "name": self.name,
            "username": self.username,
            "number_of_dishes": len(self.dishes),
            "dishes": [
                recipe.json_short()
                for recipe
                in self.dishes
            ],
        }
