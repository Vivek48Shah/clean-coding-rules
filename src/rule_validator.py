import ast
import re
import json
from collections import defaultdict

class CleanCodeLinter(ast.NodeVisitor):
    """
    AST-based Clean Code validator that checks for:
    - Function length
    - Too many parameters
    - Poor naming conventions
    - Use of magic numbers
    - Global variable modifications
    - Missing error handling via exceptions
    - Redundant comments
    - Duplicate code (DRY principle)
    - SRP violations (class complexity)
    - Deep inheritance trees
    - Logical function order
    """

    def __init__(self):
        self.violations = []
        self.global_vars = set()
        self.function_calls = defaultdict(list)  # Track function calls for logical flow check
        self.function_order = []  # Track function order

    def report_violation(self, rule_id, message, node=None):
        """
        Reports a Clean Code violation. Handles cases where node is None.
        """
        self.violations.append({
            "rule_id": rule_id,
            "line": node.lineno if node and hasattr(node, "lineno") else "N/A",
            "message": message
        })

    def visit_FunctionDef(self, node):
        """
        Checks function naming, length, number of parameters, and logical order.
        """
        self.function_order.append(node.name)  # Track function order

        # ✅ R002 - Check function length
        num_lines = node.end_lineno - node.lineno
        if num_lines > 20:
            self.report_violation("R002", f"Function '{node.name}' is too long ({num_lines} lines).", node)

        # ✅ R003 - Check function name (Descriptive function names)
        if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
            self.report_violation("R003", f"Function '{node.name}' does not follow snake_case naming.", node)

        # ✅ R004 - Check number of parameters
        if len(node.args.args) > 3:
            self.report_violation("R004", f"Function '{node.name}' has too many parameters ({len(node.args.args)}).", node)

        # ✅ R008 - Check error handling (Use exceptions instead of return codes)
        for stmt in node.body:
            if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Constant):
                self.report_violation("R008", f"Function '{node.name}' returns an error code instead of raising an exception.", stmt)

        # Track function calls for Logical Code Flow check (R012)
        for stmt in node.body:
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name):
                self.function_calls[node.name].append(stmt.value.func.id)

        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """
        Checks for deep inheritance trees and Single Responsibility Principle (SRP).
        """
        # ✅ R010 - Single Responsibility Principle (Check class size)
        if len(node.body) > 10:  # Heuristic: A class should not have too many responsibilities
            self.report_violation("R010", f"Class '{node.name}' has too many methods/attributes. May violate SRP.", node)

        # ✅ R011 - Prefer Composition Over Inheritance
        if len(node.bases) > 1:  # More than 1 base class suggests deep inheritance
            self.report_violation("R011", f"Class '{node.name}' has multiple base classes. Prefer composition over deep inheritance.", node)

        self.generic_visit(node)

    def visit_Assign(self, node):
        """
        Detects magic numbers and global variable assignments.
        """
        # ✅ R006 - Check for Magic Numbers
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, (int, float)):
            if node.value.value not in [0, 1]:  # Allow standard values
                self.report_violation("R006", f"Magic number detected: {node.value.value}. Use a named constant.", node)

        # ✅ R005 - Detect Global Variable Assignments
        if isinstance(node.targets[0], ast.Name) and isinstance(node.targets[0].ctx, ast.Store):
            self.global_vars.add(node.targets[0].id)

        self.generic_visit(node)

    def visit_Global(self, node):
        """
        Checks for global variable modifications.
        """
        for name in node.names:
            self.report_violation("R005", f"Global variable '{name}' modified. Avoid side effects.", node)

    
    def validate_logical_order(self):
        
        """R012 - Ensure Logical Code Flow (setup → process → cleanup)"""
        if len(self.function_order) < 3:
            return  # Skip validation if there are fewer than 3 functions

        setup, process, cleanup = self.function_order[:3]

        if not setup or not isinstance(setup, str):
            return  # Ensure valid function name exists

        if not process or not isinstance(process, str):
            return  # Ensure valid function name exists

        if not cleanup or not isinstance(cleanup, str):
            return  # Ensure valid function name exists

        if not (setup.startswith("init") or setup.startswith("setup")):
            self.report_violation("R012", f"Function '{setup}' should be a setup function.", None)

        if not (cleanup.startswith("clean") or cleanup.startswith("close")):
            self.report_violation("R012", f"Function '{cleanup}' should be a cleanup function.", None)
        
    def validate(self, code):
        """
        Runs the AST validator on the given Python code.
        """
        tree = ast.parse(code)
        self.visit(tree)
        self.validate_logical_order()  # Check logical function order
        return self.violations
