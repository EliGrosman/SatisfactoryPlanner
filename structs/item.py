from dataclasses import dataclass
from typing import List, TYPE_CHECKING


@dataclass
class ItemQuantity:
    """
    Represents a quantity of an item with an associated production rate.

    Attributes:
        item (Item): The item.
        quantity (float): The quantity of the item.
        rate (float): The production rate of the item (per minute).
    """
    item: "Item"
    quantity: float
    rate: float

class Item:
    """
    Represents a Satisfactory item 

    Attributes:
        itemName (str): The name of the item.
        baseRecipes (List[Recipe]): List of base recipes that produce this item.
        altRecipes (List[Recipe]): List of alternative recipes that produce this item.
    """
    def __init__(self, itemName: str):
        self.itemName: str = itemName
        self.baseRecipes: List["Recipe"] = []
        self.altRecipes: List["Recipe"] = []

    def __str__(self) -> str:
        return self.itemName
    
    def _is_base_ingredient(self):
        return len(self.baseRecipes) == 0
    
    def __repr__(self) -> str:
        return f"Item(itemName='{self.itemName}')"
    
if TYPE_CHECKING:
    from .recipe import Recipe # Import only for type checking