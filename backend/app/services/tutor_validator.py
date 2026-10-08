import re
import logging
from typing import Tuple
from app.schemas.feedback import AIFeedbackContent

logger = logging.getLogger(__name__)

class TutorValidator:
    """
    Server-side anti-solution guard and safety validator for AI Tutor responses.
    Ensures feedback remains Socratic and does NOT expose complete code solutions,
    reference solution implementations, or full program rewrites.
    """

    @staticmethod
    def validate_tutor_feedback(
        feedback: AIFeedbackContent,
        reference_solution: str = None
    ) -> Tuple[bool, str]:
        """
        Validates generated tutor feedback against anti-solution rules.
        Returns (is_valid, message).
        """
        all_text = f"{feedback.summary}\n{feedback.explanation}\n{feedback.hint}\n{feedback.next_step}"

        # Rule 1: Reject a function definition that has an actual multi-line body,
        # as opposed to a one-line mention of a function name in prose (e.g. "the
        # solve() function is where..."). Checked against the size of the matched
        # function itself, not the total length of the whole response - a short
        # response can still smuggle in a complete one-liner-looking solution.
        python_def_with_body = re.compile(
            r"def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)\s*:\s*\n(?:[ \t]+\S.*\n?){2,}"
        )
        # Also catch a complete one-liner body on the same line (def foo(): return 42),
        # distinguished from a harmless prose mention ("the solve() function is where
        # you compute X") by requiring what follows the colon to look like an actual
        # Python statement, not English.
        python_def_inline_body = re.compile(
            r"def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)\s*:\s*"
            r"(return\b|print\s*\(|yield\b|raise\b|pass\b|[a-zA-Z_][a-zA-Z0-9_]*\s*=[^=])"
        )
        if python_def_with_body.search(all_text) or python_def_inline_body.search(all_text):
            logger.warning("[TutorValidator] Rejected feedback: Contains a Python function with a real body.")
            return False, "Feedback contains a full function implementation."

        # Same idea for C/C++-style brace functions (the tutor also serves C/C++
        # submissions, and the Python-only regex above would never catch these).
        brace_function_pattern = re.compile(
            r"\b(?:int|void|float|double|char|long|short|bool|auto|unsigned)\s+"
            r"[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)\s*\{([^{}]*)\}",
            re.DOTALL,
        )
        for body in brace_function_pattern.findall(all_text):
            # Parity with the Python check above: any real statement in the body
            # (not just an empty stub) counts as a leaked implementation.
            statements = [s.strip() for s in re.split(r"[;\n]", body) if s.strip()]
            if len(statements) > 0:
                logger.warning("[TutorValidator] Rejected feedback: Contains a C/C++ function with a real body.")
                return False, "Feedback contains a full function implementation."

        # Rule 2: Reject code blocks with more than 3 lines of code
        code_block_pattern = re.compile(r"```[a-zA-Z]*\n(.*?)```", re.DOTALL)
        code_blocks = code_block_pattern.findall(all_text)
        for block in code_blocks:
            lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
            if len(lines) > 3:
                logger.warning(f"[TutorValidator] Rejected feedback: Code block contains {len(lines)} lines of code.")
                return False, "Feedback contains excessive code instead of a conceptual hint."

        # Rule 3: Reject exact reference solution leakage if provided
        if reference_solution and reference_solution.strip():
            ref_clean = "".join(reference_solution.split())
            text_clean = "".join(all_text.split())
            if len(ref_clean) > 20 and ref_clean in text_clean:
                logger.warning("[TutorValidator] Rejected feedback: Exposes exact reference solution.")
                return False, "Feedback leaks the exact reference solution."

        # Rule 4: Ensure non-empty required fields
        if not feedback.summary.strip():
            return False, "Summary field is empty."
        if not feedback.hint.strip():
            return False, "Hint field is empty."
        if not feedback.explanation.strip():
            return False, "Explanation field is empty."
        if not feedback.next_step.strip():
            return False, "Next step field is empty."

        return True, "Feedback passed tutor safety validation."
