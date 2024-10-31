import json
from collections import defaultdict
import math
from typing import List, Tuple, Dict, Union
from scipy.optimize import linprog

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

        for (output_item_name, output_amount) in output_items:
            item = self.ITEMS[output_item_name]  # Get the Item object           

            if item._is_base_ingredient():
                ingredients = [(item, output_amount)]
                machines = []
            else:
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

        

        return aggregated_ingredients, base_ingredients, aggregated_machines, total_machines
    
    def optimize(
        self,
        items: List[Tuple[str, float]], 
        alt_recipes: List[str], 
        output_items: List[Tuple[str, float]],  
    ) -> Tuple[Dict[str, float], Dict[str, float], List[Tuple[str, float]]]:
        """
        Optimizes the production of items given input resources, recipes, and desired outputs.

        Args:
            recipe_manager: An instance of RecipeManager for recipe calculations.
            items: A list of tuples representing input items and their quantities.
            alt_recipes: A list of alternative recipe names (if applicable).
            output_items: A list of tuples representing desired output items, their 
                        maximum production quantities, and their weights in the objective function.

        Returns:
            A tuple containing:
                - remaining: A dictionary of remaining input items and their quantities.
                - needed: A dictionary of items needed and their quantities.
                - output: A list of tuples representing produced output items and their quantities.
        """

        if len(items) == 0 or len(output_items) == 0:
            return None, None, None

        output_ingredients = defaultdict(lambda: defaultdict(float)) 
        all_base_items = set()
        all_items = set()
        max_outputs = [max_output for _, max_output in output_items]

        # Calculate base ingredients for each output item
        for output_item, _ in output_items:
            aggregated_ingredients, out_base_items, _, _ = \
                self.calculate_and_display_results([(output_item, 1)], alt_recipes)
            output_ingredients[output_item] = out_base_items
            all_items.update(aggregated_ingredients.keys())
            all_base_items.update(out_base_items.keys())

        # Separate base and non-base input items
        base_items = [(item, quantity) for item, quantity in items 
                    if self.ITEMS[item]._is_base_ingredient()]
        non_base_items = [(item, quantity) for item, quantity in items 
                        if not self.ITEMS[item]._is_base_ingredient()]

        # Calculate base ingredients for input items
        _, base_ingredients, _, _ = self.calculate_and_display_results(base_items, alt_recipes)
        _, non_base_base_ingredients, _, _ = self.calculate_and_display_results(non_base_items, alt_recipes)

        # Calculate coefficients for the linear program
        coeffs = {}
        for out_item in output_ingredients:
            coeffs[out_item] = [output_ingredients[out_item].get(item, 0) for item in all_base_items]

        # Calculate total input amounts for each base item
        input_amounts = []
        for key in all_base_items:
            base_ingredients.setdefault(key, 0)
            non_base_base_ingredients.setdefault(key, 0)
            input_amounts.append(base_ingredients[key] + non_base_base_ingredients[key])

        # Calculate maximum production quantities (q)
        q = []
        modified_inputs = input_amounts.copy()
        for item, rates in coeffs.items():
            qs = [x_j / max(1e-10, a_ij) for x_j, a_ij in zip(input_amounts, rates)]
            q_i = min([x for x in qs if x > 0])
            for i in range(len(input_amounts)):
                if modified_inputs[i] == 0:
                    modified_inputs[i] = rates[i] * q_i
            q.append(q_i)

        # Objective function: Maximize weighted sum of output items
        c = [-1 for i in coeffs]  # Negate for maximization

        # Inequality constraints: a_{1j}q_1 + a_{2j}q_2 + ... + a_{nj}q_n <= x_j for all j
        A_ub = []
        b_ub = []
        for j, x_j in enumerate(modified_inputs):
            row = [coeffs[item][j] for item in coeffs]
            A_ub.append(row)
            b_ub.append(x_j)

        # Add constraints for q_i <= max_output for all i
        for i in range(len(coeffs)):
            row = [0] * len(coeffs)
            row[i] = 1  # Coefficient for q_i
            A_ub.append(row)
            b_ub.append(max_outputs[i])  # No negation needed for <= constraint

        # Bounds: q_i >= 0 for all i
        bounds = [(0, None) for _ in range(len(coeffs))]

        # Solve the linear program
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

        # Extract the optimal q_i values
        optimal_outputs = result.x
        if optimal_outputs is None:
            return [], [], None

        # Format output
        output = dict(zip([x[0] for x in output_items], optimal_outputs.tolist()))
        output = [(k, v) for k, v in output.items()]

        # Calculate base ingredients for the output
        _, output_base_ingredients, _, _ = self.calculate_and_display_results(output, alt_recipes)

        # Calculate the difference between input and output ingredients
        diff = {}
        for item in base_ingredients:
            diff[item] = base_ingredients[item] - output_base_ingredients.get(item, 0)

        remaining = {k: v for k, v in diff.items() if v >= 0}
        needed = {k: -v for k, v in diff.items() if v < 0}

        return remaining, needed, output