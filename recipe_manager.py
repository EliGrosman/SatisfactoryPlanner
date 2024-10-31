import json
from collections import defaultdict
import math
from typing import List, Tuple, Dict, Union

from structs.recipe import Recipe
from structs.item import Item
from structs.machine import Machine


class RecipeManager:
    """
    Loads recipes from a JSON file and provides methods for accessing and processing them.

    Attributes:
        RECIPES (Dict[str, Recipe]): A dictionary of recipes, keyed by recipe name.
    """

    MACHINES: Dict[str, "Machine"] = {}
    ITEMS: Dict[str, "Item"] = {}
    RECIPES: Dict[str, Recipe] = {}

    def __init__(self, recipes_file: str = "recipes.json"):
        """
        Initializes the RecipeLoader by loading recipes from the specified JSON file.
        """
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
                self,
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
        alt_recipes: Dict[Item, Recipe],
        max_depth: int = 100,
        depth: int = 0,
    ) -> Union[List[Tuple[Item, float]], List[Tuple[Machine, float, Recipe]]]:
        """
        Wrapper for get_ingredients
        """
        ingredients = []
        machines = []
        self.get_ingredient(item, amount, recipe, ingredients, machines, alt_recipes, max_depth, depth)

        return ingredients, machines
        
    def get_ingredient(
        self,
        item: Item,
        amount: float,
        recipe: Recipe,
        ingredients: List[Tuple[Item, float]],
        machines: List[Tuple[Machine, float, Recipe]],
        alt_recipes: Dict[Item, Recipe],
        max_depth: int,
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
                        self.get_ingredient(
                            inp.item,
                            inp.rate * output_scalar,
                            use_recipe,
                            ingredients,
                            machines,
                            alt_recipes,
                            max_depth,
                            depth + 1,
                        )

    def calculate_and_display_results(
        self,
        output_items: List[Tuple[str, float]],
        alt_recipes_selected: List[str],
    ) -> None:
        """
        Calculates and displays the required ingredients and machines.
        """

        alt_recipes_dict = {}
        for alt_recipe_name in alt_recipes_selected:
            alt_recipe = self.RECIPES[alt_recipe_name]
            for alt_output in alt_recipe.outputs:
                alt_recipes_dict[alt_output.item] = alt_recipe

        all_ingredients = []
        all_machines = []

        for output_item_name, output_amount in output_items:
            item = self.RECIPES[output_item_name].outputs[0].item  # Get the Item object
            recipe = alt_recipes_dict.get(item, item.baseRecipes[0])

            ingredients, machines = self.get_ingredients(
                item=item,
                amount=output_amount,
                recipe=recipe,
                alt_recipes=alt_recipes_dict,
            )

            all_ingredients.extend(ingredients)
            all_machines.extend(machines)

        # Aggregate ingredients
        aggregated_ingredients = defaultdict(float)
        for item, amount in all_ingredients:
                aggregated_ingredients[item] += amount

        base_ingredients = defaultdict(float)
        for item, amount in all_ingredients:
            if(item._is_base_ingredient()):
                base_ingredients[item] += amount

        # Aggregate machines
        aggregated_machines = defaultdict(lambda: (0, ""))
        for machine, usage, recipe in all_machines:
            aggregated_machines[recipe] = (
                aggregated_machines[recipe][0] + usage,
                machine,
            )

        total_machines = defaultdict(lambda: (0, 0))
        for _, (usage, machine) in aggregated_machines.items():
            total_machines[machine] = (
                total_machines[machine][0] + math.ceil(usage),
                total_machines[machine][1] + max(1, math.floor(usage)),
            )

        # --- Sort Results ---
        sorted_ingredients = sorted(
            aggregated_ingredients.items(), key=lambda item: (-item[1], item[0].itemName)
        )  # Sort ingredients by amount (descending) then by name (ascending)

        sorted_base_ingredients = sorted(
            base_ingredients.items(), key=lambda item: (-item[1], item[0].itemName)
        )  # Sort ingredients by amount (descending) then by name (ascending)


        sorted_machines = sorted(
            aggregated_machines.items(),
            key=lambda item: (item[1][1].machineName, item[0].recipeName, item[1][0]),
        )  # Sort machines by machine name, then recipe, then usage

        sorted_total_machines = sorted(
            total_machines.items(), key=lambda item: item[0].machineName
        ) # Sort total machines by machine name

        return sorted_ingredients, sorted_base_ingredients, sorted_machines, sorted_total_machines