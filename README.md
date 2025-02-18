A Python-based tool designed to enforce clean coding standards by analyzing code for violations and providing automated fixes using Large Language Models (LLMs).

Table of Contents
	•	Introduction
	•	Design Overview
	•	Installation
	•	Usage
	•	Configuration
	•	Contributing
	•	License

Introduction

Maintaining clean and readable code is crucial for collaborative development and long-term maintenance. “Clean Coding Rules” automates the process of detecting code violations and suggests improvements, ensuring adherence to best practices.

Design Overview

The system is structured to facilitate seamless code analysis and correction through the following components:

1. Code Analysis and Violation Detection
	•	AST Parsing: Utilizes Python’s Abstract Syntax Tree (AST) module to parse the code and identify structural elements.
	•	Custom Linter (CleanCodeLinter): Analyzes the AST to detect violations of predefined clean coding rules, such as excessive function parameters or improper naming conventions.

2. Prompt Generation for LLM
	•	Prompt Generators:
	•	PromptGenerator: Creates initial prompts incorporating system instructions and coding rules.
	•	FixPromptGenerator: Generates prompts that detail detected violations and guide the LLM to provide specific fixes.

3. Iterative Code Refinement
	•	LLM Integration: Employs a Large Language Model to generate code suggestions and fixes based on the prompts.
	•	Validation Loop: The system iteratively validates the LLM’s output, re-analyzing the code and prompting for further refinements until all violations are resolved or a set iteration limit is reached.

4. Configuration and Extensibility
	•	Rule Definitions: Coding rules are defined in JSON format (configs/clean_coding_rules.json), allowing easy customization and extension.
	•	System Prompts: Initial instructions and guidelines for the LLM are stored in text files (configs/system_prompt.txt), facilitating straightforward updates.
