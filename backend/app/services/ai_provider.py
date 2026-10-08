from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class AIProvider(ABC):
    """
    Abstract Base Class for AI Question Generation and Tutoring.
    Allows easy swapping between Ollama, Mock Provider, or other future LLM engines.
    """

    @abstractmethod
    def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Sends system and user prompts to the LLM and returns the raw string response (expected to be JSON).
        Must raise an Exception if the provider is unavailable or fails.
        """
        pass

class MockAIProvider(AIProvider):
    """
    Mock AI Provider for unit tests and local development when Ollama is offline.
    Generates deterministic, valid coding problem and tutor feedback JSON.
    """

    def __init__(
        self,
        should_fail_validation: bool = False,
        should_fail_execution: bool = False,
        should_expose_solution: bool = False
    ):
        self.should_fail_validation = should_fail_validation
        self.should_fail_execution = should_fail_execution
        self.should_expose_solution = should_expose_solution

    def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[Dict[str, Any]] = None
    ) -> str:
        logger.info("[MockAIProvider] Generating mock structured JSON response...")

        # Branch 1: AI Tutor System Prompt
        if "tutor" in system_prompt.lower() or "socratic" in system_prompt.lower():
            if self.should_fail_validation:
                return "INVALID TUTOR JSON RESPONSE {"

            if self.should_expose_solution:
                return """{
  "summary": "Here is the fix",
  "error_type": "LOGIC_ERROR",
  "explanation": "You can fix your code with def solution(): return 42",
  "hint": "def solution(): print(123)",
  "next_step": "Copy-paste this code",
  "confidence": 0.99
}"""

            # Check status and hint level from user prompt
            if "ACCEPTED" in user_prompt:
                return """{
  "summary": "Your solution passed all tests successfully!",
  "error_type": "OTHER",
  "explanation": "Your implementation correctly handles all required problem cases.",
  "hint": "Consider whether variable names and structure can be polished for readability.",
  "next_step": "Think about edge cases for larger scale inputs.",
  "confidence": 0.98
}"""
            elif "RUNTIME_ERROR" in user_prompt or "Compilation" in user_prompt:
                return """{
  "summary": "Runtime error detected during execution.",
  "error_type": "RUNTIME_ERROR",
  "explanation": "Your code encountered an exception while running against test inputs.",
  "hint": "Check for array index out of bounds or invalid type conversions.",
  "next_step": "Trace your input handling line by line.",
  "confidence": 0.92
}"""
            elif "TIME_LIMIT_EXCEEDED" in user_prompt:
                return """{
  "summary": "Time Limit Exceeded.",
  "error_type": "TIME_COMPLEXITY",
  "explanation": "Your code exceeded the 5 second execution time limit.",
  "hint": "Consider whether a nested loop is causing O(N^2) complexity.",
  "next_step": "Think about using a hash map or single pass algorithm.",
  "confidence": 0.90
}"""
            elif "COMPILATION_ERROR" in user_prompt or "SYNTAX_ERROR" in user_prompt:
                return """{
  "summary": "Syntax or compilation error detected.",
  "error_type": "SYNTAX_ERROR",
  "explanation": "The interpreter could not parse your code statement.",
  "hint": "Check for missing colons, brackets, or indentation mismatches.",
  "next_step": "Inspect the line highlighted in the error message.",
  "confidence": 0.95
}"""
            else:
                # WRONG_ANSWER with progressive hint levels
                if "Hint Level 3" in user_prompt or "Level 3" in user_prompt:
                    return """{
  "summary": "Boundary logic mismatch detected.",
  "error_type": "LOGIC_ERROR",
  "explanation": "Your loop terminates one index before reaching the last element.",
  "hint": "Level 3: Compare range(len(arr)) with range(len(arr) + 1) or check your loop inequality.",
  "next_step": "Run your loop mentally on an array of size 1.",
  "confidence": 0.95
}"""
                elif "Hint Level 2" in user_prompt or "Level 2" in user_prompt:
                    return """{
  "summary": "Boundary logic mismatch detected.",
  "error_type": "LOGIC_ERROR",
  "explanation": "Your loop logic skips processing the final element in the input list.",
  "hint": "Level 2: Check whether your loop condition covers the final index.",
  "next_step": "Verify the boundary conditions of your iteration.",
  "confidence": 0.93
}"""
                else:
                    return """{
  "summary": "Logic Error in problem output.",
  "error_type": "LOGIC_ERROR",
  "explanation": "Your implementation produces incorrect output for certain input cases.",
  "hint": "Level 1: Think about which part of your loop controls how many elements are processed.",
  "next_step": "Trace your code with a small sample input on paper.",
  "confidence": 0.91
}"""

        # Branch 2: Problem Generation (Phase 4)
        if self.should_fail_validation:
            return "INVALID JSON RESPONSE {"

        if self.should_fail_execution:
            return """{
  "questions": [
    {
      "title": "Broken Factorial",
      "description": "Calculate the factorial of N.",
      "difficulty": "EASY",
      "language": "python",
      "topic": "recursion",
      "constraints": ["1 <= N <= 10"],
      "input_format": "Single integer N",
      "output_format": "Factorial of N",
      "examples": [{"input": "5", "output": "120"}],
      "test_cases": [
        {"input": "5", "expected_output": "120"},
        {"input": "3", "expected_output": "6"}
      ],
      "reference_solution": "print(99999)"
    }
  ]
}"""

        return """{
  "questions": [
    {
      "title": "Sum of First N Natural Numbers",
      "description": "Given a positive integer N, write a program to calculate and print the sum of all natural numbers from 1 to N.",
      "difficulty": "EASY",
      "language": "python",
      "topic": "math",
      "constraints": ["1 <= N <= 1000"],
      "input_format": "A single integer N.",
      "output_format": "Print the sum integer.",
      "examples": [
        {"input": "5", "output": "15"}
      ],
      "test_cases": [
        {"input": "5", "expected_output": "15"},
        {"input": "10", "expected_output": "55"}
      ],
      "reference_solution": "n = int(input())\\nprint(n * (n + 1) // 2)"
    }
  ]
}"""
