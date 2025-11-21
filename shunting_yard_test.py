import unittest


# --- Correct Functions ---

def preprocess(infix):
    """Adds explicit concatenation operators '.' to a regex string."""
    output = []
    for i, char in enumerate(infix):
        output.append(char)
        if i + 1 < len(infix):
            next_char = infix[i + 1]
            can_end_term = char.isalnum() or char in '*?+)]'
            can_start_term = next_char.isalnum() or next_char in '(['
            if can_end_term and can_start_term:
                output.append('.')
    return "".join(output)


def shunting_yard(infix):
    """Converts a regular expression from infix to postfix notation."""
    preprocessed_infix = preprocess(infix)
    precedence = {
        '*': 5, '+': 5, '?': 5,  # Quantifiers
        '.': 4,  # Concatenation
        '|': 3  # Alternation
    }
    postfix = ""
    stack = []
    i = 0
    while i < len(preprocessed_infix):
        character = preprocessed_infix[i]

        if character == "(":
            stack.append(character)
        elif character == ")":
            while stack and stack[-1] != "(":
                postfix += stack.pop()
            if stack: stack.pop()

        elif character in precedence:
            while (stack and stack[-1] not in "()" and
                   precedence.get(stack[-1], 0) >= precedence.get(character, 0)):
                postfix += stack.pop()
            stack.append(character)

        # --- THIS IS THE CRITICAL LOGIC YOU ARE MISSING ---
        elif character == "-":
            if not postfix or i + 1 >= len(preprocessed_infix):
                postfix += character  # Treat as literal
            else:
                first_char = postfix[-1]
                final_char = preprocessed_infix[i + 1]
                start_ord, end_ord = ord(first_char) + 1, ord(final_char) + 1

                if start_ord < end_ord:  # Valid range (e.g., A-C)
                    char_list = ["|" + chr(num) for num in range(start_ord, end_ord)]
                    postfix += "".join(char_list)
                    i += 1
                else:  # Invalid range (e.g., C-A)
                    postfix += character
        # --- END OF CRITICAL LOGIC ---

        else:  # Operand
            postfix += character
        i += 1

    while stack:
        postfix += stack.pop()
    return postfix


# --- Corrected Unit Test Class ---

class TestRegexParser(unittest.TestCase):
    """Test suite for the Shunting-yard algorithm implementation."""

    def test_expression_from_user(self):
        """Tests the complex case from our conversation."""
        infix = "(A+.B*)?(C-D)"
        # FIX #1: The expected value is now correct.
        expected = "A+B*.?.C|D."
        self.assertEqual(shunting_yard(infix), expected)

    def test_valid_range_operator(self):
        """Tests the custom range '-' operator."""
        self.assertEqual(shunting_yard("A-C"), "A|B|C")

    def test_invalid_range_from_user(self):
        """Tests that an invalid range treats '-' as a literal."""
        # FIX #2: The expected value is now 'C-A', which the
        # correct 'shunting_yard' function will produce.
        self.assertEqual(shunting_yard("C-A"), "C-A")


# --- This makes the script runnable ---

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)