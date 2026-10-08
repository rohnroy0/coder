"""
Fixed, built-in self-paced learning curriculum (Python / C / C++), seeded on
every startup - like Duolingo's course content, this is NOT teacher-editable.

Each language follows the same overall arc (fundamentals -> control flow ->
functions -> data structures -> paradigms -> advanced), diverging only where
a concept doesn't apply to that language (e.g. Dictionaries is Python-only;
Pointers & Memory is C/C++-only; Object-Oriented Programming is Python/C++
only - plain C has no classes).

Seeding checks whether the curriculum already seeded matches this module's
current content (by the full ordered (language, title) list). If it matches,
seeding is a no-op. If this module's content has changed since the last seed
(e.g. chapters added/reordered), the OLD system-owned curriculum is fully
replaced with the new one - this resets learning-path progress on real content
changes (there is no partial-reorder migration), but never touches anything
owned by a real teacher.
"""
import logging
import secrets
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.problem import Problem, ProblemDifficulty, ProblemStatus, TestCase
from app.models.submission import Submission
from app.models.points import StudentPointsEvent
from app.models.learning import LearningChapter, LearningChapterProblem

logger = logging.getLogger(__name__)

SYSTEM_TEACHER_EMAIL = "curriculum@system.local"
LANGUAGES = ("python", "c", "cpp")
LANGUAGE_DISPLAY_NAMES = {"python": "Python", "c": "C", "cpp": "C++"}


def _mult_table(n: int) -> str:
    return "\n".join(f"{n} x {i} = {n * i}" for i in range(1, 11))


# ─── Shared chapters: identical concept + content across all 3 languages ──

def _shared_curriculum(language: str):
    lang_name = LANGUAGE_DISPLAY_NAMES[language]
    return [
        {
            "title": f"{lang_name} Fundamentals",
            "description": "Your first steps: run a program and produce output.",
            "topic": "fundamentals", "difficulty": ProblemDifficulty.EASY,
            "problems": [
                {
                    "title": "Print Hello World",
                    "description": "Print the exact text `Hello, World!` (without quotes).",
                    "input_format": "No input.", "output_format": "A single line: Hello, World!",
                    "test_cases": [("", "Hello, World!")],
                },
                {
                    "title": "Print Your Number",
                    "description": "Read a single integer and print it back out, unchanged.",
                    "input_format": "A single integer.", "output_format": "The same integer.",
                    "test_cases": [("42", "42"), ("7", "7")],
                },
            ],
        },
        {
            "title": "Variables",
            "description": "Store and reuse values by name.",
            "topic": "variables", "difficulty": ProblemDifficulty.EASY,
            "problems": [
                {
                    "title": "Swap Using a Temporary Variable",
                    "description": "Read two integers and print them in swapped order (second, then first).",
                    "input_format": "Two space-separated integers.",
                    "output_format": "The two integers, swapped, space-separated.",
                    "test_cases": [("3 7", "7 3"), ("10 20", "20 10")],
                },
                {
                    "title": "Area of a Square",
                    "description": "Read the side length N of a square and print its area (N * N).",
                    "input_format": "A single integer N.", "output_format": "The area of the square.",
                    "test_cases": [("4", "16"), ("9", "81")],
                },
            ],
        },
        {
            "title": "Data Types",
            "description": "Work with integers and decimal (floating-point) values.",
            "topic": "data_types", "difficulty": ProblemDifficulty.EASY,
            "problems": [
                {
                    "title": "Integer Division and Remainder",
                    "description": "Read two integers A and B. Print the integer quotient and the remainder of A divided by B, space-separated.",
                    "input_format": "Two space-separated integers: A and B.",
                    "output_format": "Quotient and remainder, space-separated.",
                    "test_cases": [("17 5", "3 2"), ("20 4", "5 0")],
                },
                {
                    "title": "Average of Two Numbers",
                    "description": "Read two integers and print their average, formatted with exactly one decimal place.",
                    "input_format": "Two space-separated integers.",
                    "output_format": "The average, with exactly one decimal place (e.g. 3.5).",
                    "test_cases": [("3 4", "3.5"), ("5 5", "5.0")],
                },
            ],
        },
        {
            "title": "Operators",
            "description": "Combine values with arithmetic and comparison operators.",
            "topic": "operators", "difficulty": ProblemDifficulty.EASY,
            "problems": [
                {
                    "title": "Arithmetic Operators Practice",
                    "description": "Read two integers A and B. Print A+B, then A-B, then A*B, each on its own line.",
                    "input_format": "Two space-separated integers.",
                    "output_format": "Three lines: sum, difference, product.",
                    "test_cases": [("10 3", "13\n7\n30"), ("6 2", "8\n4\n12")],
                },
                {
                    "title": "Compare Two Numbers",
                    "description": "Read two integers. Print 1 if the first is greater, -1 if the second is greater, or 0 if they are equal.",
                    "input_format": "Two space-separated integers.",
                    "output_format": "1, -1, or 0.",
                    "test_cases": [("5 3", "1"), ("2 8", "-1")],
                },
            ],
        },
        {
            "title": "Input / Output",
            "description": "Read multiple values and format your output.",
            "topic": "io", "difficulty": ProblemDifficulty.EASY,
            "problems": [
                {
                    "title": "Sum of Three Numbers",
                    "description": "Read three space-separated integers on one line and print their sum.",
                    "input_format": "Three space-separated integers.", "output_format": "Their sum.",
                    "test_cases": [("1 2 3", "6"), ("10 20 30", "60")],
                },
                {
                    "title": "Formatted Output",
                    "description": "Read an integer N and print it inside the sentence `The value is: N`.",
                    "input_format": "A single integer N.", "output_format": "The value is: N",
                    "test_cases": [("5", "The value is: 5"), ("100", "The value is: 100")],
                },
            ],
        },
        {
            "title": "Conditions",
            "description": "Branch your program's behavior based on a condition.",
            "topic": "conditions", "difficulty": ProblemDifficulty.EASY,
            "problems": [
                {
                    "title": "Even or Odd",
                    "description": "Read an integer and print `Even` if it is even, otherwise `Odd`.",
                    "input_format": "A single integer.", "output_format": "Even or Odd.",
                    "test_cases": [("4", "Even"), ("7", "Odd")],
                },
                {
                    "title": "Maximum of Two Numbers",
                    "description": "Read two integers and print the larger of the two.",
                    "input_format": "Two space-separated integers.", "output_format": "The larger integer.",
                    "test_cases": [("3 9", "9"), ("12 5", "12")],
                },
            ],
        },
        {
            "title": "Loops",
            "description": "Repeat work with for/while loops.",
            "topic": "loops", "difficulty": ProblemDifficulty.EASY,
            "problems": [
                {
                    "title": "Sum of First N Natural Numbers",
                    "description": "Read an integer N and print 1 + 2 + ... + N.",
                    "input_format": "A single integer N.", "output_format": "The sum of the first N natural numbers.",
                    "test_cases": [("5", "15"), ("10", "55")],
                },
                {
                    "title": "Factorial of a Number",
                    "description": "Read an integer N and print N! (N factorial).",
                    "input_format": "A single integer N (0 <= N <= 12).", "output_format": "N factorial.",
                    "test_cases": [("5", "120"), ("6", "720")],
                },
            ],
        },
        {
            "title": "Nested Loops",
            "description": "Combine loops inside loops to produce shaped or tabular output.",
            "topic": "nested_loops", "difficulty": ProblemDifficulty.MEDIUM,
            "problems": [
                {
                    "title": "Right Triangle of Stars",
                    "description": "Read an integer N and print a right triangle of stars: line i (from 1 to N) contains i asterisk characters, with no trailing spaces.",
                    "input_format": "A single integer N.", "output_format": "N lines; line i has i '*' characters.",
                    "test_cases": [("3", "*\n**\n***"), ("4", "*\n**\n***\n****")],
                },
                {
                    "title": "Multiplication Table",
                    "description": "Read an integer N and print its multiplication table from 1 to 10, one line per entry in the format `N x i = result`.",
                    "input_format": "A single integer N.",
                    "output_format": "10 lines in the form N x i = result, for i = 1 to 10.",
                    "test_cases": [("5", _mult_table(5)), ("3", _mult_table(3))],
                },
            ],
        },
        {
            "title": "Functions",
            "description": "Organize logic into reusable, named blocks.",
            "topic": "functions", "difficulty": ProblemDifficulty.MEDIUM,
            "problems": [
                {
                    "title": "Check Prime Number",
                    "description": "Read an integer N and print `Prime` if it is a prime number, otherwise print `Not Prime`.",
                    "input_format": "A single integer N (N >= 2).", "output_format": "Prime or Not Prime.",
                    "test_cases": [("7", "Prime"), ("10", "Not Prime")],
                },
                {
                    "title": "GCD of Two Numbers",
                    "description": "Read two integers and print their Greatest Common Divisor (GCD).",
                    "input_format": "Two space-separated integers.", "output_format": "Their GCD.",
                    "test_cases": [("12 18", "6"), ("17 5", "1")],
                },
            ],
        },
        {
            "title": "Parameters & Arguments",
            "description": "Pass values into a function and use them.",
            "topic": "parameters", "difficulty": ProblemDifficulty.MEDIUM,
            "problems": [
                {
                    "title": "Power of a Number",
                    "description": "Write a function that takes a base and an exponent as parameters and returns base raised to the power exponent. Read both, then print the result.",
                    "input_format": "Two space-separated integers: base and exponent (exponent >= 0).",
                    "output_format": "base raised to the power exponent.",
                    "test_cases": [("2 10", "1024"), ("3 4", "81")],
                },
                {
                    "title": "Minimum of Three Numbers",
                    "description": "Write a function taking three numbers as parameters and returning the smallest. Read three integers, then print the smallest.",
                    "input_format": "Three space-separated integers.", "output_format": "The smallest of the three.",
                    "test_cases": [("5 2 8", "2"), ("10 10 3", "3")],
                },
            ],
        },
        {
            "title": "Recursion",
            "description": "Solve problems by having a function call itself.",
            "topic": "recursion", "difficulty": ProblemDifficulty.MEDIUM,
            "problems": [
                {
                    "title": "Fibonacci Number",
                    "description": "Read an integer N (0-indexed) and print the Nth Fibonacci number, where F(0)=0 and F(1)=1.",
                    "input_format": "A single integer N (0 <= N <= 30).", "output_format": "The Nth Fibonacci number.",
                    "test_cases": [("6", "8"), ("10", "55")],
                },
                {
                    "title": "Sum of Digits (Recursive)",
                    "description": "Read a positive integer N and print the sum of its digits, using recursion (peel off the last digit and recurse on the rest).",
                    "input_format": "A single positive integer N.", "output_format": "The sum of N's digits.",
                    "test_cases": [("1234", "10"), ("905", "14")],
                },
            ],
        },
    ]


# ─── Data-structure / paradigm chapters: diverge per language ─────────────

LISTS_CHAPTER = {
    "title": "Lists",
    "description": "Store and process an ordered, resizable sequence of values.",
    "topic": "lists", "difficulty": ProblemDifficulty.MEDIUM,
    "problems": [
        {
            "title": "Sum of a List",
            "description": "Read an integer N, then N space-separated integers. Print their sum.",
            "input_format": "N on the first line; N space-separated integers on the second.",
            "output_format": "The sum of the N integers.",
            "test_cases": [("4\n1 2 3 4", "10"), ("3\n5 10 15", "30")],
        },
        {
            "title": "Find Maximum in List",
            "description": "Read an integer N, then N space-separated integers. Print the largest one.",
            "input_format": "N on the first line; N space-separated integers on the second.",
            "output_format": "The largest integer.",
            "test_cases": [("4\n3 7 2 9", "9"), ("3\n1 1 1", "1")],
        },
    ],
}

TUPLES_CHAPTER = {
    "title": "Tuples",
    "description": "Group fixed, ordered values together - often returned together from a function.",
    "topic": "tuples", "difficulty": ProblemDifficulty.MEDIUM,
    "problems": [
        {
            "title": "Swap Values Using Tuple Unpacking",
            "description": "Read two integers and print them swapped (second, then first), using tuple unpacking (e.g. a, b = b, a).",
            "input_format": "Two space-separated integers.",
            "output_format": "The two integers, swapped, space-separated.",
            "test_cases": [("1 9", "9 1"), ("4 6", "6 4")],
        },
        {
            "title": "Area and Perimeter",
            "description": "Read the width and height of a rectangle. Print its area and perimeter as two space-separated values, as if returning both from one function as a tuple.",
            "input_format": "Two space-separated integers: width and height.",
            "output_format": "Area and perimeter, space-separated.",
            "test_cases": [("4 5", "20 18"), ("3 3", "9 12")],
        },
    ],
}

SETS_CHAPTER = {
    "title": "Sets",
    "description": "Work with collections of unique values.",
    "topic": "sets", "difficulty": ProblemDifficulty.MEDIUM,
    "problems": [
        {
            "title": "Count Unique Elements",
            "description": "Read an integer N, then N integers. Print the number of distinct values among them.",
            "input_format": "N on the first line; N space-separated integers on the second.",
            "output_format": "The count of distinct values.",
            "test_cases": [("5\n1 2 2 3 3", "3"), ("4\n4 4 4 4", "1")],
        },
        {
            "title": "Common Elements Count",
            "description": "Read list A (its size then its integers), then list B (its size then its integers). Print how many distinct values appear in both lists.",
            "input_format": "N, then N integers (list A); then M, then M integers (list B).",
            "output_format": "The number of values common to both lists.",
            "test_cases": [("3\n1 2 3\n3\n2 3 4", "2"), ("2\n5 6\n2\n7 8", "0")],
        },
    ],
}

DICTIONARIES_CHAPTER = {
    "title": "Dictionaries",
    "description": "Map keys to values for fast lookup.",
    "topic": "dictionaries", "difficulty": ProblemDifficulty.MEDIUM,
    "problems": [
        {
            "title": "Most Frequent Character",
            "description": "Read a single word (lowercase letters, no spaces) and print its most frequently occurring character. The tests never contain a tie.",
            "input_format": "A single word.", "output_format": "The most frequent character.",
            "test_cases": [("aabbbcc", "b"), ("xxyz", "x")],
        },
        {
            "title": "Count Occurrences of a Word",
            "description": "Read an integer N, then N space-separated words, then a target word. Print how many times the target word appears among the N words.",
            "input_format": "N; then N space-separated words; then the target word.",
            "output_format": "The number of times the target word appears.",
            "test_cases": [("5\na b a c a\na", "3"), ("4\nx y z x\ny", "1")],
        },
    ],
}

ARRAYS_CHAPTER = {
    "title": "Arrays",
    "description": "Store and process a fixed-size sequence of values.",
    "topic": "arrays", "difficulty": ProblemDifficulty.MEDIUM,
    "problems": [
        {
            "title": "Sum of an Array",
            "description": "Read an integer N, then N space-separated integers. Print their sum.",
            "input_format": "N on the first line; N space-separated integers on the second.",
            "output_format": "The sum of the N integers.",
            "test_cases": [("4\n1 2 3 4", "10"), ("3\n5 10 15", "30")],
        },
        {
            "title": "Find Maximum in Array",
            "description": "Read an integer N, then N space-separated integers. Print the largest one.",
            "input_format": "N on the first line; N space-separated integers on the second.",
            "output_format": "The largest integer.",
            "test_cases": [("4\n3 7 2 9", "9"), ("3\n1 1 1", "1")],
        },
    ],
}

STRINGS_CHAPTER = {
    "title": "Strings",
    "description": "Process and transform text.",
    "topic": "strings", "difficulty": ProblemDifficulty.MEDIUM,
    "problems": [
        {
            "title": "Reverse a String",
            "description": "Read a line of text and print it reversed.",
            "input_format": "A single line of text (no spaces).", "output_format": "The text, reversed.",
            "test_cases": [("hello", "olleh"), ("python", "nohtyp")],
        },
        {
            "title": "Count Vowels",
            "description": "Read a line of text and print how many vowels (a, e, i, o, u, either case) it contains.",
            "input_format": "A single line of text.", "output_format": "The number of vowels.",
            "test_cases": [("hello world", "3"), ("PYTHON", "1")],
        },
    ],
}

POINTERS_CHAPTER = {
    "title": "Pointers & Memory",
    "description": "Work with memory addresses directly instead of only by value.",
    "topic": "pointers", "difficulty": ProblemDifficulty.HARD,
    "problems": [
        {
            "title": "Swap Two Numbers",
            "description": "Read two integers and print them swapped (second, then first). Practice swapping the values via pointers / pass-by-reference before printing.",
            "input_format": "Two space-separated integers.",
            "output_format": "The two integers, swapped, space-separated.",
            "test_cases": [("2 8", "8 2"), ("15 25", "25 15")],
        },
        {
            "title": "Find Minimum Using Pointers",
            "description": "Read an integer N, then N space-separated integers. Print the minimum value. Practice iterating with a pointer to the array instead of indexing.",
            "input_format": "N on the first line; N space-separated integers on the second line.",
            "output_format": "The minimum integer in the list.",
            "test_cases": [("4\n8 3 9 1", "1"), ("3\n5 5 5", "5")],
        },
    ],
}

STRUCTURES_CHAPTER = {
    "title": "Structures",
    "description": "Group related fields together into one custom type.",
    "topic": "structures", "difficulty": ProblemDifficulty.MEDIUM,
    "problems": [
        {
            "title": "Point Distance Squared",
            "description": "Read the coordinates of two points, x1 y1 x2 y2. Model each as a Point structure and print the squared distance between them: (x2-x1)^2 + (y2-y1)^2.",
            "input_format": "Four space-separated integers: x1 y1 x2 y2.",
            "output_format": "The squared distance between the two points.",
            "test_cases": [("0 0 3 4", "25"), ("2 3 2 7", "16")],
        },
        {
            "title": "Student Average Marks",
            "description": "Read three integer marks for a student. Model them in a Student structure and print the average, using integer division.",
            "input_format": "Three space-separated integers.", "output_format": "The integer-division average of the three marks.",
            "test_cases": [("80 90 70", "80"), ("50 60 70", "60")],
        },
    ],
}

OOP_CHAPTER = {
    "title": "Object-Oriented Programming",
    "description": "Model data and behavior together using classes.",
    "topic": "oop", "difficulty": ProblemDifficulty.HARD,
    "problems": [
        {
            "title": "Rectangle Area",
            "description": "Read the width and height of a rectangle and print its area. Practice modeling this with a Rectangle class that stores width and height and computes the area.",
            "input_format": "Two space-separated integers: width and height.",
            "output_format": "The area (width * height).",
            "test_cases": [("4 5", "20"), ("3 3", "9")],
        },
        {
            "title": "Bank Account Balance",
            "description": "Read a starting balance, then an integer N, then N transaction amounts (positive for deposit, negative for withdrawal). Print the final balance. Practice modeling this with a BankAccount class that tracks balance and applies transactions through a method.",
            "input_format": "Starting balance on the first line; N on the second line; N space-separated transaction amounts on the third line.",
            "output_format": "The final balance after applying all transactions.",
            "test_cases": [("100\n3\n50 -30 20", "140"), ("0\n2\n-10 10", "0")],
        },
    ],
}

VECTORS_CHAPTER = {
    "title": "Vectors",
    "description": "Use the STL vector, a resizable array container.",
    "topic": "vectors", "difficulty": ProblemDifficulty.MEDIUM,
    "problems": [
        {
            "title": "Sum of a Vector",
            "description": "Read an integer N, then N space-separated integers into a vector. Print their sum.",
            "input_format": "N on the first line; N space-separated integers on the second.",
            "output_format": "The sum of the N integers.",
            "test_cases": [("3\n10 20 30", "60"), ("5\n1 1 1 1 1", "5")],
        },
        {
            "title": "Append and Sum",
            "description": "Read an integer N, then N space-separated integers into a vector, then one more integer X. Push X onto the vector and print the new total sum.",
            "input_format": "N; then N space-separated integers; then X.",
            "output_format": "The sum of all N+1 values.",
            "test_cases": [("3\n1 2 3\n10", "16"), ("2\n5 5\n0", "10")],
        },
    ],
}


def _advanced_chapter():
    return {
        "title": "Advanced Concepts",
        "description": "Combine what you've learned to search and sort data.",
        "topic": "advanced", "difficulty": ProblemDifficulty.HARD,
        "problems": [
            {
                "title": "Linear Search",
                "description": "Read an integer N, then N space-separated integers, then a target integer X. Print the 1-based position of X in the list, or -1 if it does not appear.",
                "input_format": "N; then N space-separated integers; then X.",
                "output_format": "The 1-based index of X, or -1 if not found.",
                "test_cases": [("5\n4 2 7 1 9\n7", "3"), ("3\n1 2 3\n5", "-1")],
            },
            {
                "title": "Bubble Sort (Ascending)",
                "description": "Read an integer N, then N space-separated integers. Print them sorted in ascending order, space-separated.",
                "input_format": "N on the first line; N space-separated integers on the second line.",
                "output_format": "The N integers sorted ascending, space-separated.",
                "test_cases": [("5\n5 3 4 1 2", "1 2 3 4 5"), ("4\n4 3 2 1", "1 2 3 4")],
            },
        ],
    }


def full_curriculum_for(language: str):
    """The complete, ordered chapter sequence for one language."""
    shared = _shared_curriculum(language)
    if language == "python":
        return shared + [LISTS_CHAPTER, TUPLES_CHAPTER, SETS_CHAPTER, DICTIONARIES_CHAPTER,
                          OOP_CHAPTER, _advanced_chapter()]
    if language == "c":
        return shared + [ARRAYS_CHAPTER, STRINGS_CHAPTER, STRUCTURES_CHAPTER,
                          POINTERS_CHAPTER, _advanced_chapter()]
    if language == "cpp":
        return shared + [ARRAYS_CHAPTER, STRINGS_CHAPTER, POINTERS_CHAPTER, STRUCTURES_CHAPTER,
                          OOP_CHAPTER, VECTORS_CHAPTER, _advanced_chapter()]
    raise ValueError(f"No curriculum defined for language: {language}")


def _get_or_create_system_teacher(db: Session) -> User:
    user = db.query(User).filter(User.email == SYSTEM_TEACHER_EMAIL).first()
    if user:
        return user
    user = User(
        name="Learning Path Curriculum",
        email=SYSTEM_TEACHER_EMAIL,
        password_hash=get_password_hash(secrets.token_urlsafe(32)),
        role=UserRole.TEACHER,
    )
    db.add(user)
    db.flush()
    return user


def _curriculum_is_up_to_date(db: Session) -> bool:
    expected = {
        (language, chapter_def["title"])
        for language in LANGUAGES
        for chapter_def in full_curriculum_for(language)
    }
    actual = {
        (row.language, row.title)
        for row in db.query(LearningChapter.language, LearningChapter.title)
    }
    return expected == actual


def _wipe_system_curriculum(db: Session, system_teacher_id: int) -> None:
    """Removes every chapter/problem/test-case/submission/points-event owned by
    the system curriculum account, in FK-safe order, via explicit bulk deletes
    (not relying on ORM or DB-level cascade, since SQLite FK enforcement may be
    off). Never touches anything owned by a real teacher."""
    problem_ids = [row[0] for row in db.query(Problem.id).filter(Problem.created_by == system_teacher_id)]
    chapter_ids = [row[0] for row in db.query(LearningChapter.id).filter(LearningChapter.created_by == system_teacher_id)]

    if problem_ids:
        submission_ids = [
            row[0] for row in db.query(Submission.id).filter(Submission.problem_id.in_(problem_ids))
        ]
        if submission_ids:
            db.query(StudentPointsEvent).filter(StudentPointsEvent.submission_id.in_(submission_ids)).delete(synchronize_session=False)
            db.query(Submission).filter(Submission.id.in_(submission_ids)).delete(synchronize_session=False)
        db.query(TestCase).filter(TestCase.problem_id.in_(problem_ids)).delete(synchronize_session=False)

    if chapter_ids:
        db.query(LearningChapterProblem).filter(LearningChapterProblem.chapter_id.in_(chapter_ids)).delete(synchronize_session=False)
        db.query(LearningChapter).filter(LearningChapter.id.in_(chapter_ids)).delete(synchronize_session=False)

    if problem_ids:
        db.query(Problem).filter(Problem.id.in_(problem_ids)).delete(synchronize_session=False)

    db.flush()
    db.expire_all()  # bulk deletes bypass the identity map; drop stale cached state


def seed_learning_curriculum(db: Session) -> None:
    """
    Idempotent fast path: no-op if the DB's (language, title) chapter set
    already matches this module's curriculum exactly. Otherwise, replaces the
    system-owned curriculum entirely with the current content (see module
    docstring for what that resets).
    """
    if _curriculum_is_up_to_date(db):
        return

    system_teacher = _get_or_create_system_teacher(db)
    _wipe_system_curriculum(db, system_teacher.id)

    for language in LANGUAGES:
        for order, chapter_def in enumerate(full_curriculum_for(language), start=1):
            chapter = LearningChapter(
                language=language, title=chapter_def["title"], description=chapter_def["description"],
                order=order, created_by=system_teacher.id,
            )
            db.add(chapter)
            db.flush()

            for problem_order, problem_def in enumerate(chapter_def["problems"], start=1):
                problem = Problem(
                    title=problem_def["title"], description=problem_def["description"],
                    difficulty=chapter_def["difficulty"], status=ProblemStatus.VERIFIED,
                    topic=chapter_def["topic"], language=language,
                    input_format=problem_def["input_format"], output_format=problem_def["output_format"],
                    created_by=system_teacher.id,
                )
                db.add(problem)
                db.flush()

                for tc_input, tc_output in problem_def["test_cases"]:
                    db.add(TestCase(problem_id=problem.id, input=tc_input, expected_output=tc_output))

                db.add(LearningChapterProblem(chapter_id=chapter.id, problem_id=problem.id, order=problem_order))

    db.commit()
    logger.info("[Curriculum] Learning-path curriculum (re)seeded.")
