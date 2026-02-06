import sys
import os
import yaml
from src.parser import HPLParser
from src.evaluator import HPLEvaluator


def main():
    if len(sys.argv) != 2:
        print("Usage: python interpreter.py <hpl_file>")
        sys.exit(1)

    hpl_file = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(hpl_file):
        print(f"Error: File '{hpl_file}' not found.")
        sys.exit(1)

    try:
        parser = HPLParser(hpl_file)
        classes, objects, main_func = parser.parse()

        evaluator = HPLEvaluator(classes, objects, main_func)
        evaluator.run()
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML syntax - {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: An unexpected error occurred - {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
