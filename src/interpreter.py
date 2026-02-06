import sys
from src.parser import HPLParser
from src.evaluator import HPLEvaluator

def main():
    if len(sys.argv) != 2:
        print("Usage: python interpreter.py <hpl_file>")
        sys.exit(1)

    hpl_file = sys.argv[1]
    parser = HPLParser(hpl_file)
    classes, objects, main_func, call_target = parser.parse()

    evaluator = HPLEvaluator(classes, objects, main_func, call_target)
    evaluator.run()

if __name__ == "__main__":
    main()

