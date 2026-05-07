"""
Condition checking behavior nodes
"""
import py_trees


class Condition(py_trees.behaviour.Behaviour):
    """Check a boolean condition"""
    
    def __init__(self, condition_name: str, condition):
        super().__init__(name=f'Condition{condition_name}')
        self.condition = condition
        self.condition_name = condition_name

    def update(self) -> py_trees.common.Status:
        result = self.condition()
        print(f"{self.condition_name}: {result}")
        
        return (py_trees.common.Status.SUCCESS if result 
                else py_trees.common.Status.FAILURE)