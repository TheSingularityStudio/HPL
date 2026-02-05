import sys
from src.parser import HPLParser
from src.evaluator import HPLEvaluator

def main():
    if len(sys.argv) != 2:
        print("Usage: python interpreter.py <hpl_file>")
        sys.exit(1)

    hpl_file = sys.argv[1]
    with open(hpl_file, 'r', encoding='utf-8') as f:
        yaml_content = f.read()

    parser = HPLParser(yaml_content)
    classes, objects, main_func = parser.parse()

    evaluator = HPLEvaluator(classes, objects, main_func)
    evaluator.run()

if __name__ == "__main__":
    main()
