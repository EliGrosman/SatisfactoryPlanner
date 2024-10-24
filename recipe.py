from typing import Dict, Union, List

MACHINES = {}
ITEMS = {}

class Item():
    def __init__(self, itemName: str):
        self.itemName: str = itemName
        self.baseRecipes: List[Recipe] = []
        self.altRecipes: List[Recipe] = []

    def __str__(self):
        return self.itemName

class Machine():
    def __init__(self, machineName: str):
        self.machineName: str = machineName

class Recipe():
    def __init__(self, recipeName: str, time: float, machineName: str, outputs: Union[Item, float, float], inputs: Union[Item, float, float], type: str):
        self.recipeName: str = recipeName
        self.time: float = time
        self.type: str = type

        if machineName in MACHINES.keys():
            self.machine: Machine = MACHINES[machineName]
        else:
            machine = Machine(machineName=machineName)
            self.machine: Machine = machine
            MACHINES[machineName] = machine

        outs: Union[Item, float, float] = []
        for output in outputs:
            if output[0] in ITEMS.keys():
                item: Item = ITEMS[output[0]]
            else:
                item: Item = Item(output[0])
                ITEMS[output[0]] = item
            
            outs.append((item, output[1], output[2]))

        ins: Union[Item, float, float] = []
        for input in inputs:
            if input[0] in ITEMS.keys():
                item: Item = ITEMS[input[0]]
            else:
                item: Item = Item(input[0])
                ITEMS[input[0]] = item
            
            ins.append((item, input[1], input[2]))

        self.outputs: Union[Item, float, float] = outs
        self.inputs: Union[Item, float, float] = ins

        if self.type == "base":
            for output in self.outputs:
                out: Item = output[0]
                if self.recipeName == out.itemName:
                    ITEMS[out.itemName].baseRecipes.append(self)
        else:
            for output in self.outputs:
                out: Item = output[0]
                ITEMS[out.itemName].altRecipes.append(self)

    def __str__(self):
        return f"Recipe: {self.recipeName}"
    
    def print(self):
        lines: List[str] = []
        lines.append(f"{self.recipeName} ({self.type})")
        if self.type == "manual":
            lines.append(f"   Manual: x {self.time}")
        else:
            lines.append(f"   {self.machine.machineName} ({self.time} secs)")

        lines.append("   Outputs:")
        for item in self.outputs:
            lines.append(f"     {item[0]} x{item[1]} ({item[2]} / min)")

        lines.append("   Inputs:")
        for item in self.inputs:
            lines.append(f"     {item[0]} x{item[1]} ({item[2]} / min)")

        return "\n".join(lines)

        
