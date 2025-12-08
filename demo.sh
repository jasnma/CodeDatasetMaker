#!/bin/bash

echo "=== Code Dataset Maker Demo ==="
echo

echo "1. Generating function call graph for test_project..."
python3 c_graph.py test_project
echo

echo "2. Generating file tree for test_project (with default output)..."
python3 generate_file_tree.py test_project
echo

echo "3. Generating function call graph for test_struct_macro..."
python3 c_graph.py test_struct_macro
echo

echo "4. Generating file tree for test_struct_macro (with custom JSON output)..."
python3 generate_file_tree.py test_struct_macro -o test_struct_macro_tree.json
echo

echo "=== Demo Complete ==="
echo "Check the output directory for generated files."
