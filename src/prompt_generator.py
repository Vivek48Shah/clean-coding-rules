import json

class PromptGenerator:

    def __init__(self, system_prompt_path: str, rules_path: str, instructions_path: str):
        self.system_prompt_path = system_prompt_path
        self.rules_path = rules_path
        self.instructions_path = instructions_path
        self.system_prompt = self._load_file(self.system_prompt_path)
        self.rules = self._load_rules()
        self.final_instructions = self._load_final_instructions()

    def _load_file(self, path: str) -> str:
        """Loads text files."""
        with open(path, "r") as file:
            return file.read().strip()

    def _load_rules(self) -> str:
        """Loads and formats Clean Code rules from JSON."""
        with open(self.rules_path, "r") as file:
            rules = json.load(file)
        return "\n".join([f"{rule['id']} {rule['name']} - {rule['description']}" for rule in rules["rules"]])

    def _load_final_instructions(self) -> str:
        """Loads final instructions from JSON."""
        with open(self.instructions_path, "r") as file:
            instructions = json.load(file)["instructions"]
        return "\n".join([f"{instr}" for instr in instructions])

    def generate_prompt(self, user_query: str) -> str:
        """Generates the final structured prompt."""
        return f"""
{self.system_prompt}

---
**Clean Code Rules:**
{self.rules}

---
**User Query:** {user_query}

---
{self.final_instructions}
"""

