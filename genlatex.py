import random
import argparse

def generate_problem_latex(operation_type: str, max_stack_height: int) -> str:
    """Generates a single arithmetic problem in LaTeX format."""
    
    n_numbers = random.randint(2, max_stack_height)
    
    numbers = []
    operators = []

    # Number generation logic based on stack height and operation type
    if n_numbers == 2:
        num1 = random.randint(10, 999) # First number generally larger
        num2 = random.randint(1, 99)   # Second number often smaller
        
        if operation_type == "minus" or (operation_type == "mix" and random.choice([True, False])):
            # Ensure num1 > num2 for subtraction
            if num1 <= num2:
                # Swap and ensure num1 is significantly larger for a sensible problem
                num1, num2 = num2 + random.randint(10, 50), num1 
            
            numbers.append(num1)
            numbers.append(num2)
            operators.append('-')
        else: # Addition for n_numbers = 2
            numbers.append(num1)
            numbers.append(num2)
            operators.append('+')
            
    else: # n_numbers = 3 or 4 (multi-operand problems)
        # For multiple numbers, typically addition problems, keep numbers somewhat smaller
        for _ in range(n_numbers):
            numbers.append(random.randint(1, 99)) # Numbers up to 2 digits for multiple operands
            
        for _ in range(n_numbers - 1):
            if operation_type == "plus":
                operators.append('+')
            elif operation_type == "mix":
                # Decision: For multiple numbers in 'mix' mode, use only addition to avoid complexity
                operators.append('+')
            # 'minus' case is forced to n_numbers=2 and handled above
            
    # Construct LaTeX string
    latex_parts = []
    
    # Add all numbers except the very last one, without an operator
    for i in range(n_numbers - 1):
        latex_parts.append(f" {numbers[i]} ")

    # Get the operator for the last number (which is always the last operator in the list)
    last_op_char = operators[-1]

    # Append the last number with its operator
    latex_parts.append(f" {last_op_char}{numbers[n_numbers-1]} ")

    # Join with newlines for LaTeX array
    problem_latex = " \\\\\n".join(latex_parts)
    
    # Add the horizontal line
    problem_latex += " \\\\\n \\hline "

    # Wrap in array environment
    return f"$ \\begin{{array}}{{r}}\n{problem_latex}\n\\end{{array}} $"


def generate_latex_document(operation_type: str, num_problems_per_row: int = 5, num_rows: int = 10, max_stack_height: int = 4) -> str:
    """Generates the full LaTeX document content."""

    header = r"""\documentclass{article}
\usepackage{amsmath} %% Required for the align environment, etc.
\usepackage{geometry} %% For page margins
\geometry{a4paper, margin=1in} %% Set margins

\begin{document}
\centering

\begin{tabular}{*{%s}{c}}
""" % num_problems_per_row

    footer = r"""\end{tabular}

\end{document}"""

    problems_content = []
    for r in range(num_rows):
        row_problems = []
        for c in range(num_problems_per_row):
            row_problems.append(generate_problem_latex(operation_type, max_stack_height))
        problems_content.append(" & ".join(row_problems))
        
        # Add a \\ at the end of each row except the last
        if r < num_rows - 1:
            problems_content[-1] += " \\\\"
        
        problems_content[-1] += "\n" # Add a newline after each row

    return header + "".join(problems_content) + footer


def main():
    parser = argparse.ArgumentParser(description="Generate LaTeX arithmetic problems.")
    parser.add_argument(
        "operation",
        choices=["plus", "minus", "mix"],
        help="Type of operation: 'plus', 'minus', or 'mix'."
    )
    parser.add_argument(
        "-o", "--output",
        default="output.tex",
        help="Output file name for the LaTeX document (default: output.tex)."
    )
    parser.add_argument(
        "-s", "--stack_height",
        type=int,
        choices=range(2, 5), # Valid choices are 2, 3, 4
        default=4,
        help="Maximum stack height for numbers (2 to 4, default: 4)."
    )
    parser.add_argument(
        "-t", "--total_problems",
        type=int,
        default=50, # Default to 50 problems (10 rows * 5 problems/row)
        help="Total number of problems to generate (default: 50). Will be rounded up to the nearest multiple of 5."
    )

    args = parser.parse_args()

    # Calculate rows and problems per row based on total problems
    num_problems_per_row = 5 # Fixed as per latext.txt structure
    num_rows = (args.total_problems + num_problems_per_row - 1) // num_problems_per_row # Ceil division
    if num_rows == 0: num_rows = 1 # Ensure at least one row for problems

    # Ensure max_stack_height is within allowed range (2 to 4)
    actual_max_stack_height = max(2, min(args.stack_height, 4))

    latex_output = generate_latex_document(
        operation_type=args.operation,
        num_problems_per_row=num_problems_per_row,
        num_rows=num_rows,
        max_stack_height=actual_max_stack_height
    )

    with open(args.output, "w") as f:
        f.write(latex_output)
    
    print(f"Generated LaTeX problems saved to {args.output}")

if __name__ == "__main__":
    main()
