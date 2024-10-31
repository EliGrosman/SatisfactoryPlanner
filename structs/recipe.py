from typing import List, Tuple
from .item import Item, ItemQuantity 
from .machine import Machine

class Recipe:
    """
    Represents a recipe for producing items.

    Attributes:
        recipeName (str): The name of the recipe.
        time (float): The time required to complete the recipe.
        machine (Machine): The machine used in the recipe.
        outputs (List[ItemQuantity]): List of output item quantities.
        inputs (List[ItemQuantity]): List of input item quantities.
        type (str): The type of the recipe ("base" or "alt").
    """
    def __init__(self, recipeManager, recipeName: str, time: float, machineName: str, 
                 outputs: List[Tuple[str, float, float]], 
                 inputs: List[Tuple[str, float, float]], 
                 type: str):
        self.recipeManager = recipeManager
        self.recipeName: str = recipeName
        self.time: float = time
        self.type: str = type

        self.machine: Machine = self._get_or_create_machine(machineName)

        self.outputs: List[ItemQuantity] = [
            ItemQuantity(item=self._get_or_create_item(item_name), quantity=quantity, rate=rate) 
            for item_name, quantity, rate in outputs
        ]
        self.inputs: List[ItemQuantity] = [
            ItemQuantity(item=self._get_or_create_item(item_name), quantity=quantity, rate=rate) 
            for item_name, quantity, rate in inputs
        ]

        self._add_recipe_to_items()

    def __repr__(self) -> str:
        return f"Recipe(recipeName='{self.recipeName}')" 

    def _get_or_create_machine(self, machineName: str) -> Machine:
        """Retrieves a machine from MACHINES or creates a new one if it doesn't exist."""
        machine = self.recipeManager.MACHINES.get(machineName)
        if not machine:
            machine = Machine(machineName=machineName)
            self.recipeManager.MACHINES[machineName] = machine
        return machine

    def _get_or_create_item(self, itemName: str) -> Item:
        """Retrieves an item from ITEMS or creates a new one if it doesn't exist."""
        item = self.recipeManager.ITEMS.get(itemName)
        if not item:
            item = Item(itemName)
            self.recipeManager.ITEMS[itemName] = item
        return item

    def _add_recipe_to_items(self) -> None:
        """Adds the recipe to the corresponding item's recipe list."""
        for output in self.outputs:
            item = output.item
            if item.itemName == self.recipeName and self.type != "alternate":
                self.recipeManager.ITEMS[item.itemName].baseRecipes.append(self)
            else:
                self.recipeManager.ITEMS[item.itemName].altRecipes.append(self)

    def __str__(self) -> str:
        return f"Recipe: {self.recipeName}"

    def print(self) -> str:
        """Provides a formatted string representation of the recipe."""
        lines: List[str] = []
        lines.append(f"{self.recipeName} ({self.type})")
        if self.type == "manual":
            lines.append(f"   Manual: x {self.time}")
        else:
            lines.append(f"   {self.machine.machineName} ({self.time} secs)")

        lines.append("   Outputs:")
        for item_quantity in self.outputs:
            lines.append(f"     {item_quantity.item} x{item_quantity.quantity} ({item_quantity.rate} / min)")

        lines.append("   Inputs:")
        for item_quantity in self.inputs:
            lines.append(f"     {item_quantity.item} x{item_quantity.quantity} ({item_quantity.rate} / min)")

        return "\n".join(lines)