import lightning as L
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from src.rule_validator import CleanCodeLinter
from src.prompt_generator import PromptGenerator
from src.fix_prompt_generator import FixPromptGenerator


class CleanCodePipeline(L.LightningWork):
    """Lightning AI Work to Run LLM, Validate Code, and Fix Violations Iteratively."""

    def __init__(self):
        super().__init__(cloud_compute="gpu")  # Use Lightning AI's free GPU
        self.model_name = "mistralai/Mistral-7B-Instruct"  # Open-source LLM
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name, torch_dtype=torch.float16, device_map="auto")
        
        # Initialize prompt generators
        self.prompt_generator = PromptGenerator(
            "configs/system_prompt.txt",
            "configs/clean_code_rules.json",
            "configs/final_instructions.json"
        )
        self.fix_generator = FixPromptGenerator("configs/final_instructions.json")

    def generate_response(self, user_query):
        """Generates LLM response for a given user query."""
        inputs = self.tokenizer(user_query, return_tensors="pt").to("cuda")
        outputs = self.model.generate(**inputs, max_length=512)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

    def validate_code(self, code):
        """Runs the AST validator on the LLM-generated code."""
        linter = CleanCodeLinter()
        violations = linter.validate(code)
        return violations

    def iterative_fix_loop(self, original_code, max_iterations=1):
        """Runs iterative validation and fixes on LLM output."""
        current_code = original_code
        iteration = 0

        while iteration < max_iterations:
            print(f"\n🛠 Iteration {iteration+1}: Validating Code Fixes...\n")
            violations = self.validate_code(current_code)

            if not violations:
                print("✅ No violations found. Code is clean!")
                return current_code

            print("🚨 Detected Violations:", violations)

            # Generate fix prompt
            fix_prompt = self.fix_generator.generate_fix_prompt(
                current_code, violations, expected_behavior="The function should execute as intended."
            )
            print("\nGenerated Fix Prompt for LLM:\n", fix_prompt)

            # Get the fixed code from LLM
            fixed_code = self.generate_response(fix_prompt)

            # Re-validate the fixed code
            new_violations = self.validate_code(fixed_code)
            print("\nNew Violations after fix:", new_violations)

            if not new_violations:
                print("✅ Final fixed code is valid!")
                return fixed_code

            current_code = fixed_code
            iteration += 1

        print("❌ Max iterations reached. Returning last fixed version.")
        return current_code

    def run(self, user_query):
        """Main function to execute the clean code pipeline."""
        
        user_query = input("\n Enter your coding task/query: ")
        # Step 1: Get LLM-generated response
        llm_prompt = self.prompt_generator.generate_prompt(user_query)
        llm_output = self.generate_response(llm_prompt)
        print("\n📌 Initial LLM Output:\n", llm_output)

        # Step 2: Validate and fix code
        final_code = self.iterative_fix_loop(llm_output)

        print("\n✅ Final Clean Code:\n", final_code)
        return final_code


class CleanCodeApp(L.LightningFlow):
    """Main Lightning Flow to run the clean code pipeline."""
    def __init__(self):
        super().__init__()
        self.pipeline = CleanCodePipeline()

    def run(self, user_query):
        """Execute the clean code pipeline with the given user query."""
        final_output = self.pipeline.run(user_query)
        print("\n🚀 Final Output:\n", final_output)


app = CleanCodeApp()