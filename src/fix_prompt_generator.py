import json
import os 
class FixPromptGenerator:
    """Generates a structured Chain of Thought (CoT) prompt for an LLM to fix detected Clean Code violations."""

    def __init__(self, prompt_file="prompt/fixing_approach.txt"):
        self.prompt_file = prompt_file
        self.fixing_approach = None  # Lazy load

    def _load_fixing_approach(self):
        if self.fixing_approach is None:
            if not os.path.exists(self.prompt_file):
                raise FileNotFoundError(f"Fixing approach file not found: {self.prompt_file}")
            with open(self.prompt_file, "r", encoding="utf-8") as file:
                self.fixing_approach = file.read()


    def find_function_name(self, line_number: int, code_lines: list) -> str:
        """
        Given a line number, find the nearest function name above it.
        Returns the function name if found; otherwise, returns None.
        """
        for i in range(line_number - 1, -1, -1):
            line = code_lines[i].strip()
            if line.startswith("def "):
                # Extract and return the function name
                return line.split("(")[0].replace("def ", "").strip()
        return None

    def format_violations(self, violations: list, original_code: str) -> str:
        """
        Formats violations to be specific, stating exactly which function (or global) has the issue.
        """
        violation_details = []
        code_lines = original_code.split("\n")

        for v in violations:
            line_number = v.get("line", "N/A")
            rule_id = v.get("rule_id", "Unknown")
            message = v.get("message", "No message provided.")

            function_name = None
            if isinstance(line_number, int) and 1 <= line_number <= len(code_lines):
                function_name = self.find_function_name(line_number, code_lines)

            if function_name:
                violation_details.append(
                    f"**Function `{function_name}` (Line {line_number})** - **Rule {rule_id}**: {message}"
                )
            else:
                violation_details.append(
                    f"**Global Issue (Line {line_number})** - **Rule {rule_id}**: {message}"
                )

        return "\n".join(violation_details)

    def generate_fix_prompt(self, original_code: str, violations: list) -> str:
        """
        Generate a structured Chain of Thought prompt for the LLM to fix the detected violations.
        """
        if not violations:
            return "No violations detected. No fixes needed."

        self._load_fixing_approach()

        formatted_violations = self.format_violations(violations, original_code)

        prompt = f""" 
Detected Clean Code Violations:
{formatted_violations}

---
{self.fixing_approach}

---
**Original Code:**
{original_code}
"""
        return prompt.strip()
