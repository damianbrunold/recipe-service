# Recipe-Service

## Overview

This is a simple Service which provides an API to handle cooking recipes and menus.
Through this API, you can create, update, delete and view recipes. You can collect
recipes into menus.

There are different roles for managing permissions for recipes
and for menus. In addition, an administrator role is provided. The authorization
is handled by Auth0. The API is hosted on Heroku. The base URL is:

https://....

The project was created as the capstone project of the Udacity Fullstack Web Developer Nanodegree.

## Project set up

...

## API Reference

### List recipes

```
GET /recipe
GET /recipe?page=2
```

Returns the paged list of recipes. Each page consists of at most 10
recipes. Select pages by specifying the `page` request parameter.

This endpoint is public and does not require authentication.

Sample result:

```
{
  "page": 1,
  "recipes": [
    {
      "id": 1,
      "name": "Simple salad",
      "username": "test@example.com"
    },
    {
      "id": 2,
      "name": "Tofu",
      "username": "recipe@recipe.dabr.ch"
    }
  ],
  "success": true,
  "total_pages": 1
}
```

### Get recipe

```
GET /recipe/1
```

Returns the details of the recipe with recipe_id=1.

This endpoint is public and does not require authentication.

Sample result:

```
{
  "recipe": {
    "id": 1,
    "ingredients": [
      {
        "amount": 1.0,
        "name": "Lettuce"
      },
      {
        "amount": 2.0,
        "name": "teaspoons of vinegar"
      },
      {
        "amount": 3.0,
        "name": "teaspoons of olive oil"
      },
      {
        "amount": 1.0,
        "name": "salt and pepper"
      },
      {
        "amount": 1.0,
        "name": "bundle of chives"
      }
    ],
    "name": "Simple salad",
    "preparation": "1. wash and cut lettuce, 2. mix vinegar, oil, salt and pepper into a vinaigrette, 3. mix lettuce and vinaigrette, 4. serve",
    "servings": 4,
    "username": "test@example.com"
  },
  "success": true
}
```

### Add recipe

```
POST /recipe
```

Creates a new recipe in the database.

Requires `add:recipe` permission.

Sample body:

```
{
    "name": "Simple salad",
    "servings": 4,
    "ingredients": [
      {
        "amount": 1.0,
        "name": "Lettuce"
      },
      {
        "amount": 2.0,
        "name": "teaspoons of vinegar"
      },
      {
        "amount": 3.0,
        "name": "teaspoons of olive oil"
      },
      {
        "amount": 1.0,
        "name": "salt and pepper"
      },
      {
        "amount": 1.0,
        "name": "bundle of chives"
      }
    ],
    "preparation": "1. wash and cut lettuce, 2. mix vinegar, oil, salt and pepper into a vinaigrette, 3. mix lettuce and vinaigrette, 4. serve"
}
```

Sample result:

```
{
  "id": 9,
  "msg": "Added recipe with id 9",
  "success": true
}
```

### Update recipe

```
PATCH /recipe/1
```

Updates an existing recipe.

It is possible to provide a body with a full recipe json specification (as in the `POST /recipe` endpoint).

Alternatively, it is possible to just provide the fields that change.

If the ingredient list is changed, then the full ingredients list must be provided. It is not possible to
selectively update ingredients.

Requires `update:recipe` permission. It is not possible to update a recipe of a different user (unless
the current user has administrative privileges, i.e. the `update:any-recipe` permission).

Sample body:

```
{
    "name": "Simple small salad",
    "servings": 2
}
```

Sample result:

```
{
  "id": 1,
  "msg": "Updated recipe with id 1",
  "success": true
}
```

### Delete recipe

```
DELETE /recipe/1
```

Deletes an existing recipe.

A recipe cannot be deleted if it is contained in any menu.

Requires `delete:recipe` permission. It is not possible to delete a recipe of a different user (unless
the current user has administrative privileges, i.e. the `delete:any-recipe` permission).


Sample result:

```
{
  "id": 1,
  "msg": "Recipe 1 deleted",
  "success": true
}
```

### List menus

```
GET /menu
GET /menu?page=2
```

Returns the paged list of menus. Each page consists of at most 10
menus. Select pages by specifying the `page` request parameter.

This endpoint is public and does not require authentication.

Sample result:

```
{
  "menus": [
    {
      "id": 1,
      "name": "Testmenu",
      "username": "test@example.com"
    }
  ],
  "page": 1,
  "success": true,
  "total_pages": 1
}
```

### Get menu

```
GET /menu/1
```

Returns the details of the menu with menu_id=1.

This endpoint is public and does not require authentication.

Sample result:

```
{
  "menu": {
    "dishes": [
      {
        "id": 1,
        "name": "Simple salad",
        "username": "test@example.com"
      },
      {
        "id": 2,
        "name": "Tofu",
        "username": "test@example.com"
      },
      {
        "id": 3,
        "name": "Chocolate dessert",
        "username": "test@example.com"
      }
    ],
    "id": 1,
    "name": "Testmenu",
    "number_of_dishes": 3,
    "username": "test@example.com"
  },
  "success": true
}
```

### Add menu

```
POST /menu
```

Creates a new menu in the database.

Requires `add:menu` permission.

Sample body:

```
{
    "name": "Simple Menu",
    "dishes": [
      {"recipe_id": 1},
      {"recipe_id": 2}
    ]
}
```

Sample result:

```
{
  "id": 4,
  "msg": "Added menu with id 4",
  "success": true
}
```

### Update menu

```
PATCH /menu/1
```

Updates an existing menu.

It is possible to provide a body with a full menu json specification (as in the `POST /menu` endpoint).

Alternatively, it is possible to just provide the fields that change.

If the dishes list is changed, then the full dishes list must be provided. It is not possible to
selectively update dishes.

Requires `update:menu` permission. It is not possible to update a menu of a different user (unless
the current user has administrative privileges, i.e. the `update:any-menu` permission).

Sample body:

```
{
    "name": "Festive menu"
}
```

Sample result:

```
{
  "id": 1,
  "msg": "Updated menu with id 1",
  "success": true
}
```

### Delete menu

```
DELETE /menu/1
```

Deletes an existing menu.

Deleting a menu does not delete its constituent dishes/recipes.

Requires `delete:menu` permission. It is not possible to delete a menu of a different user (unless
the current user has administrative privileges, i.e. the `delete:any-menu` permission).


Sample result:

```
{
  "id": 1,
  "msg": "Menu 1 deleted",
  "success": true
}
```


## Auth0 test users

For testing purposes, there are three test users set up:

User `recipe@recipe.dabr.ch` with password `test-recipe-1234` has permission to handle recipes.

User `menu@recipe.dabr.ch` with password `test-menu-1234` has permission to handle menus.

User `admin@recipe.dabr.ch` with password `test-admin-1234` has full permissions.
