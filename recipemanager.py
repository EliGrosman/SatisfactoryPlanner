from typing import Dict, List, Tuple

from structs import Item, Recipe, Machine

import json

class RecipeManager:
    """
    Loads recipes from a JSON file and provides methods for accessing and processing them.

    Attributes:
        RECIPES (Dict[str, Recipe]): A dictionary of recipes, keyed by recipe name.
    """

    def __init__(self, recipes_file: str = "recipes.json"):
        """
        Initializes the RecipeLoader by loading recipes from the specified JSON file.
        """
        self.RECIPES: Dict[str, Recipe] = {}
        self._load_recipes(recipes_file)

    def _load_recipes(self, recipes_file: str) -> None:
        """
        Loads recipes from the given JSON file.
        """
        with open(recipes_file) as f:
            recipes_json = json.load(f)

        for recipe_data in recipes_json:
            outputs = [
                (i["item"], i["amount"], i["perMin"]) for i in recipe_data["outputs"]
            ]
            inputs = [
                (i["item"], i["amount"], i["perMin"]) for i in recipe_data["inputs"]
            ]

            self.RECIPES[recipe_data["name"]] = Recipe(
                recipe_data["name"],
                recipe_data["time"],
                recipe_data["machine"],
                outputs,
                inputs,
                recipe_data["type"],
            )

    def get_recipes_by_type(self, recipe_type: str) -> Dict[str, Recipe]:
        """
        Returns a dictionary of recipes filtered by the specified type.

        Args:
            recipe_type (str): The type of recipes to retrieve.

        Returns:
            Dict[str, Recipe]: A dictionary of recipes matching the given type.
        """
        return {
            name: recipe
            for name, recipe in self.RECIPES.items()
            if recipe.type == recipe_type
        }

    def get_ingredients(
        self,
        item: Item,
        amount: float,
        recipe: Recipe,
        ingredients: List[Tuple[Item, float]],
        machines: List[Tuple[Machine, float, Recipe]],
        max_depth: int,
        alt_recipes: Dict[Item, Recipe],
        depth: int = 0,
    ) -> None:
        """
        Recursively calculates the required ingredients and machines for producing a given item.

        Args:
            item (Item): The item to produce.
            amount (float): The desired amount of the item.
            recipe (Recipe): The recipe to use for producing the item.
            ingredients (List[Tuple[Item, float]]): A list to store the required ingredients 
                                                   (modified in-place).
            machines (List[Tuple[Machine, float, Recipe]]): A list to store the required machines and 
                                                            their usage (modified in-place).
            max_depth (int): The maximum recursion depth.
            alt_recipes (Dict[Item, Recipe]): A dictionary of alternative recipes to use.
            depth (int): The current recursion depth.
        """
        if depth >= max_depth:
            return

        for output in recipe.outputs:
            if output.item == item:
                output_scalar = amount / output.rate
                machines.append(
                    (recipe.machine, output_scalar, recipe)
                )

                for inp in recipe.inputs:
                    ingredients.append((inp.item, inp.rate * output_scalar))

                    use_recipe = alt_recipes.get(inp.item) or (
                        inp.item.baseRecipes[0] if inp.item.baseRecipes else None
                    )

                    if use_recipe:
                        self.get_ingredients(
                            inp.item,
                            inp.rate * output_scalar,
                            use_recipe,
                            ingredients,
                            machines,
                            max_depth,
                            alt_recipes,
                            depth + 1,
                        )