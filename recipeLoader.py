from recipe import Item, Recipe, Machine, ITEMS
from typing import List, Tuple, Union, Dict
import json

class RecipeLoader():
    def __init__(self):
        # load recipes
        with open("recipes.json") as f:
            recipes_json = json.load(f)

        self.RECIPES = {}
        for recipe in recipes_json:

            outputs = [(i["item"], i["amount"], i["perMin"]) for i in recipe["outputs"]]
            inputs = [(i["item"], i["amount"], i["perMin"]) for i in recipe["inputs"]]

            self.RECIPES[recipe["name"]] = Recipe(recipe["name"], recipe["time"], recipe["machine"], outputs, inputs, recipe["type"])

    def getRecipyByType(self, type: str):
        new = {}
        for recipeName in self.RECIPES.keys():
            if self.RECIPES[recipeName].type == type:
                new[recipeName] = self.RECIPES[recipeName]
        return new
    
    def get_ings(self, item: Item, amount, recipe: Recipe, ings: Union[Item, float], machs: Union[Machine, float, str], maxL, alt_recipes: Dict[Item, Recipe], l=0):
        # break early
        if maxL < l:
            return
        
        # make sure we're getting the right "output" from the recipe. Only really matters for recipes where it's a secondary output
        for out in recipe.outputs:
            if out[0] == item:
                # we have the correct output

                # output scalar. Guessed and it worked
                out_scalar = amount / out[2]

                machs.append((recipe.machine.machineName, out_scalar, recipe.recipeName))

                # iterate over inputs to get their materials
                
                for inp in recipe.inputs:

                    # add scaled value
                    ings.append((inp[0].itemName, inp[2] * out_scalar))
                    

                    # use alt recipe, else use base recipe
                    if inp[0] in alt_recipes.keys():
                        use_recipe = alt_recipes[inp[0]]
                    elif len(inp[0].baseRecipes) > 0:
                        use_recipe = inp[0].baseRecipes[0]
                    else:
                        return
                    
                    # keep going deeper to get ingreds for ingredients that need to be crafted. i.e. not raw materials
                    self.get_ings(inp[0], inp[2] * out_scalar, use_recipe, ings, machs, maxL, alt_recipes, l+1)
