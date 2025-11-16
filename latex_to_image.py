import argparse
import re
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np

def generate_image_from_latex_file(input_filepath: str, output_filepath: str):
    """
    Reads a file containing LaTeX math code, extracts array environments,
    and generates a single image file from them.

    Args:
        input_filepath: Path to the input file containing LaTeX.
        output_filepath: Path for the output image file (e.g., .png, .jpg).
    """
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            latex_content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_filepath}' not found.")
        return
    except Exception as e:
        print(f"Error reading input file: {e}")
        return

    # First, try to extract the content within \begin{document}...\end{document}
    # This handles full LaTeX files like latext.txt
    document_content_match = re.search(r'\\begin\{document\}(.*?)\\end\{document\}', latex_content, re.DOTALL)
    if document_content_match:
        processed_content = document_content_match.group(1)
    else:
        processed_content = latex_content # If no document environment, use full content

    # Next, try to extract content within \begin{tabular}...\end{tabular}
    # This handles structures found in latext.txt where math arrays are inside a tabular.
    tabular_content_match = re.search(r'\\begin\{tabular\}\{.*?\}\s*(.*?)\s*\\end\{tabular\}', processed_content, re.DOTALL)
    if tabular_content_match:
        processed_content = tabular_content_match.group(1)
    # If no tabular environment, processed_content remains as it was (document content or full file content)

    # First, find all content delimited by $...$ (potential math expressions).
    # This handles cases where math blocks are separated by & or \\.
    all_raw_math_expressions = re.findall(r'\$(.*?)\$', processed_content, re.DOTALL)

    math_blocks = []
    for raw_expr in all_raw_math_expressions:
        # Now, within each raw expression (the content between $ and $),
        # look for the actual array environment, making sure it constitutes the main content.
        array_match = re.search(r'^\s*(\\begin\{array\}.*?\\end\{array\})\s*$', raw_expr, re.DOTALL)
        if array_match:
            math_blocks.append(array_match.group(1).strip()) # Add the captured array content, stripped of whitespace

    if not math_blocks:
        print("No LaTeX array environments found in the input file.")
        return

    # Determine grid size for subplots
    num_blocks = len(math_blocks)
    
    # Heuristic for grid layout: try to keep it somewhat square
    ncols = int(np.ceil(np.sqrt(num_blocks)))
    # Ensure ncols is not too small if num_blocks is large (e.g., 10 blocks, sqrt is 3.16, so ncols=4, rows=3)
    # Or if num_blocks is small (e.g., 2 blocks, sqrt is 1.4, so ncols=2, rows=1)
    if num_blocks > 0:
        nrows = int(np.ceil(num_blocks / ncols))
    else:
        nrows = 0

    # Disable LaTeX rendering for the figure to avoid external LaTeX dependency.
    # Matplotlib's internal mathtext engine will be used.
    plt.rcParams['text.usetex'] = False

    # Create a figure and subplots
    fig: Figure = plt.figure(figsize=(ncols * 2.5, nrows * 1.5)) # Adjust figsize as needed
    canvas = FigureCanvasAgg(fig) # Use Agg backend for non-interactive generation

    for i, latex_block in enumerate(math_blocks):
        ax = fig.add_subplot(nrows, ncols, i + 1)
        ax.axis('off') # Hide axes

        # Transform the LaTeX array block into a mathtext-compatible string.
        # This simplifies the array environment to multi-line text, losing
        # specific array formatting like precise column alignment and exact hline appearance.
        # It's a compromise to avoid needing an external LaTeX installation.
        # Transform the LaTeX array block into a mathtext-compatible string,
        # manually handling alignment for arithmetic display.

        # Remove array environment delimiters
        block_content = latex_block.replace('\\begin{array}{r}', '').replace('\\end{array}', '')
        # Remove any remaining '&' which shouldn't be present in {r} columns but for safety.
        block_content = block_content.replace('&', '')

        raw_lines = block_content.split('\\\\')

        parsed_lines_data = []
        max_number_part_len = 0 # Max length of the numerical part (e.g., '72', '11')
        has_operator_column = False # Flag to determine if an operator column is needed

        for line_content in raw_lines:
            line_content = line_content.strip()
            if not line_content:
                continue

            hline_match = re.search(r'\\hline', line_content)
            if hline_match:
                parsed_lines_data.append({'type': 'hline'})
            else:
                operator = ''
                number_string = line_content

                if number_string.startswith('+') or number_string.startswith('-'):
                    operator = number_string[0]
                    number_string = number_string[1:].strip()
                    has_operator_column = True
                
                # Update max_number_part_len
                max_number_part_len = max(max_number_part_len, len(number_string))
                
                parsed_lines_data.append({
                    'type': 'number',
                    'operator': operator,
                    'number_string': number_string
                })
        
        # Calculate the total width needed for the numeric part plus an optional operator column.
        # The operator column will be 2 characters wide (e.g., '+ ' or '  ').
        operator_col_width = 2 if has_operator_column else 0
        
        # Determine the maximum required width for the entire content block (numbers + operators).
        # Also, ensure that horizontal lines have a minimum aesthetic length (e.g., '-----').
        min_hline_width = 5 
        calculated_content_width = max_number_part_len + operator_col_width
        final_display_width = max(calculated_content_width, min_hline_width)

        aligned_output_lines = []
        for line_data in parsed_lines_data:
            if line_data['type'] == 'hline':
                aligned_output_lines.append('-' * final_display_width)
            else: # type == 'number'
                # Pad the number part to ensure right alignment within its sub-column.
                padded_number = line_data['number_string'].rjust(max_number_part_len)
                
                # Construct the operator prefix ('+ ', '- ', or '  ')
                operator_prefix = ''
                if has_operator_column:
                    if line_data['operator']:
                        operator_prefix = line_data['operator'] + ' '
                    else:
                        operator_prefix = '  '

                full_line_content = operator_prefix + padded_number
                aligned_output_lines.append(full_line_content)

        simplified_latex_block = '\n'.join(aligned_output_lines)
        
        # Render the pre-aligned simplified LaTeX block as plain text.
        # horizontalalignment='right' ensures the entire block aligns to the right
        # of the subplot, maintaining the internal right-alignment of numbers.
        ax.text(0.5, 0.5, simplified_latex_block,
                horizontalalignment='right',
                verticalalignment='center',
                fontsize=18, # Adjust font size as needed
                transform=ax.transAxes,
                usetex=False)
        
        # Adjust layout to prevent overlapping
        plt.tight_layout(rect=[0, 0.03, 1, 0.97]) # Adjust rect to leave space for potential titles if needed

    # Save the figure
    try:
        fig.savefig(output_filepath, bbox_inches='tight', pad_inches=0.1)
        print(f"Image successfully generated and saved to '{output_filepath}'")
    except Exception as e:
        print(f"Error saving image: {e}")
    finally:
        plt.close(fig) # Close the figure to free up memory

def main():
    parser = argparse.ArgumentParser(
        description="Generate an image from a file containing LaTeX math code (specifically array environments)."
    )
    parser.add_argument(
        "input_file",
        help="Path to the input file containing LaTeX math expressions."
    )
    parser.add_argument(
        "output_file",
        help="Path to the output image file (e.g., output.png, output.jpg)."
    )

    args = parser.parse_args()
    generate_image_from_latex_file(args.input_file, args.output_file)

if __name__ == "__main__":
    main()
