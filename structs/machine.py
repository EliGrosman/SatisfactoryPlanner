class Machine:
    """
    Represents a Satisfactory machine

    Attributes:
        machineName (str): The name of the machine.
    """
    def __init__(self, machineName: str):
        self.machineName: str = machineName

    def __str__(self) -> str:
        return self.machineName
    
    def __repr__(self) -> str:
        return f"Machine(machineName='{self.machineName}')"