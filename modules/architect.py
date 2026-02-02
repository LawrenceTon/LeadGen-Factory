import json
import os
from typing import List, Dict

class ArchitectLogic:
    def __init__(self, recipes_dir="recipes"):
        self.recipes_dir = recipes_dir
        self.ensure_recipes_dir()

    def ensure_recipes_dir(self):
        if not os.path.exists(self.recipes_dir):
            os.makedirs(self.recipes_dir)

    def save_recipe(self, name: str, columns: List[Dict[str, str]]) -> bool:
        """
        Saves a recipe to a JSON file.
        
        Args:
            name: The name of the recipe.
            columns: A list of dictionaries, e.g., [{"col_name": "Job Title", "keywords": "CEO"}]
            
        Returns:
            True if successful, False otherwise.
        """
        if not name:
            return False
            
        filename = f"{name}.json"
        filepath = os.path.join(self.recipes_dir, filename)
        
        data = {
            "name": name,
            "columns": columns
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving recipe: {e}")
            return False

    def load_recipes(self) -> List[str]:
        """
        Returns a list of all .json files in the recipes folder.
        """
        try:
            files = [f for f in os.listdir(self.recipes_dir) if f.endswith('.json')]
            return files
        except Exception as e:
            print(f"Error loading recipes: {e}")
            return []
