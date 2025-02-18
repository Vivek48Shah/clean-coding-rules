import json

class FixPromptGenerator:
    """Generates a structured Chain of Thought (CoT) prompt for an LLM to fix detected Clean Code violations."""

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
        Generates a structured Chain of Thought prompt for the LLM to fix the detected violations.
        """
        if not violations:
            return "No violations detected. No fixes needed."

        formatted_violations = self.format_violations(violations, original_code)

        prompt = f""" 
Detected Clean Code Violations:
{formatted_violations}

---
### Step-by-Step Fixing Approach (Chain of Thought)
1. Understand the Code & Expected Behavior:
   - Ensure that after applying fixes, the functionality remains unchanged.
2. Analyze the Reported Issues:
- Identify the specific lines where violations occur.
- Understand why each issue is a violation.
3. Make Minimal Fixes to Correct Only the Reported Violations
- Do NOT introduce new Clean Code violations
- Ensure that the fixed code still produces the expected output

---
** Original Code:**
{original_code}

"""
        return prompt.strip()
