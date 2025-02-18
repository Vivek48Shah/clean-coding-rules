import lightning as L
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from src.rule_validator import CleanCodeLinter
from src.prompt_generator import PromptGenerator
from src.fix_prompt_generator import FixPromptGenerator
import re

class CleanCodePipeline(L.LightningModule):
    def __init__(self):
        super().__init__()  # Use Lightning AI's free GPU
        self.model_name = "deepseek-ai/deepseek-coder-6.7b-base"  
        self._model = None# Open-source LLM
        self._tokenizer = None  # Will be loaded later in setup()
        self.setup()  
        # self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        # self.model = AutoModelForCausalLM.from_pretrained(self.model_name, torch_dtype=torch.float16, device_map="auto")
        
    
    def setup(self):
        """Load tokenizer, model, and initialize prompt generators."""
        # Load non-JSON-serializable objects in setup()
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name, token=True)
        self._model = AutoModelForCausalLM.from_pretrained(self.model_name, token=True)
        
        self._model.to("cuda") 
        
        self.prompt_generator = PromptGenerator(
            "/prompts/SystemPrompt.txt",
            "/prompts/clean_coding_rules.json",
            "/prompts/final_instructions.json"
        )
        self.fix_generator = FixPromptGenerator()

    def generate_response(self, user_query):
        """Generates LLM response for a given user query."""
        if self._tokenizer is None or self._model is None:
            self.setup()
        
        inputs = self._tokenizer(user_query, return_tensors="pt").to("cuda")
        outputs = self._model.generate(**inputs, max_new_tokens=1000)
        return self._tokenizer.decode(outputs[0], skip_special_tokens=True)

    def validate_code(self, code):
        """Runs the AST validator on the LLM-generated code."""
        code = code.replace("≤", "<=").replace("≥", ">=")
        code = code.replace("→", "->") 
        code = re.sub(r"```[\w]*\n?", "", code) # If LLM generates arrow symbols
    
        # Remove any other non-ASCII characters
        code = re.sub(r'[^\x00-\x7F]+', '', code) 
        linter = CleanCodeLinter()
        violations = linter.validate(code)
        return violations

    def iterative_fix_loop(self, original_code, max_iterations=1):
        """Runs iterative validation and fixes on LLM output."""
        current_code = original_code
        iteration = 0

        while iteration < max_iterations:
            print(f"\n Iteration {iteration+1}: Validating Code Fixes...\n")
            violations = self.validate_code(current_code)

            if not violations:
                print(" No violations found. Code is clean!")
                return current_code

            print(" Detected Violations:", violations)

            # Generate fix prompt
            fix_prompt = self.fix_generator.generate_fix_prompt(
                current_code, violations
            )
            print("\nGenerated Fix Prompt for LLM:\n", fix_prompt)

            # Get the fixed code from LLM
            fixed_code = self.generate_response(fix_prompt)

            # Re-validate the fixed code
            new_violations = self.validate_code(fixed_code)
            print("\nNew Violations after fix:", new_violations)

            if not new_violations:
                print("Final fixed code is valid!")
                return fixed_code

            current_code = fixed_code
            iteration += 1

        print(" Max iterations reached. Returning last fixed version.")
        return current_code

    def run(self, user_query):
        """Main function to execute the clean code pipeline."""
        
    
        # Step 1: Get LLM-generated response
        llm_prompt = self.prompt_generator.generate_prompt(user_query)
        llm_output = self.generate_response(llm_prompt)
        print("\n Initial LLM Output:\n", llm_output)

        cleaned_text = re.sub(r"\*+", "", llm_output)

        # Find the word "Solution" (case-insensitive) and extract all words after it
        match = re.search(r"(?i)\bSolution\b:\s*(.*)", cleaned_text)  # Looks for 'Solution' as a whole word
        if match:
            solution_text = match.group(1)
            #print(solution_text)
            final_code = self.iterative_fix_loop(str(solution_text))  
        else:   
            
            # Step 2: Validate and fix code
            final_code = self.iterative_fix_loop(llm_output)

        print("\nFinal Clean Code:\n", final_code)
        return final_code


class CleanCodeApp(L.LightningModule):
    """Main Lightning Flow to run the clean code pipeline."""
    def __init__(self):
        super().__init__()
        self.pipeline = CleanCodePipeline()

    def run(self, user_query):
        """Execute the clean code pipeline with the given user query."""
        final_output = self.pipeline.run(user_query)
        print("\nFinal Output:\n", final_output)


if __name__ == "__main__":
    
    test_query = "Write a code function to fetch stock prices and display on ui"
    
    # Instantiate the app
    app = CleanCodeApp()
    
    # Run the pipeline with the test query and capture the output.
    output = app.run(test_query)
    
    # Print the final output.
    print("\n Final Output from Standalone Run:\n", output)
