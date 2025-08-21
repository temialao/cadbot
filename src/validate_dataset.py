#!/usr/bin/env python3
"""
Dataset validation script for CadQuery training data.
Validates JSONL format, content quality, CadQuery code syntax, and dynamic execution.
"""

import json
import ast
import re
import sys
import tempfile
import os
from typing import Dict, List, Tuple, Any
from pathlib import Path

# Import CadQuery for dynamic validation
try:
    import cadquery as cq
    CADQUERY_AVAILABLE = True
except ImportError:
    CADQUERY_AVAILABLE = False


class DatasetValidator:
    def __init__(self, dataset_path: str, enable_dynamic_validation: bool = True):
        self.dataset_path = Path(dataset_path)
        self.enable_dynamic_validation = enable_dynamic_validation and CADQUERY_AVAILABLE
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.temp_dir = tempfile.mkdtemp(prefix="cadbot_validation_") if self.enable_dynamic_validation else None
        
    def __del__(self):
        """Clean up temporary files."""
        import shutil
        if hasattr(self, 'temp_dir') and self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def validate(self) -> Tuple[bool, List[Dict], List[Dict]]:
        """
        Validate the entire dataset.
        Returns: (is_valid, errors, warnings)
        """
        print(f"Validating dataset: {self.dataset_path}")
        if self.enable_dynamic_validation:
            print("Dynamic execution validation: ENABLED")
        else:
            print("Static validation only: Dynamic execution DISABLED")
            if not CADQUERY_AVAILABLE:
                print("CadQuery not available. Install with: pip install cadquery>=2.4.0")
        
        if not self.dataset_path.exists():
            self.errors.append({
                "line": 0,
                "type": "file_error",
                "message": f"Dataset file not found: {self.dataset_path}"
            })
            return False, self.errors, self.warnings
        
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            self._validate_line(line_num, line.strip())
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
    
    def _validate_line(self, line_num: int, line: str) -> None:
        """Validate a single line of the dataset."""
        
        # Skip empty lines
        if not line.strip():
            if line_num != len(open(self.dataset_path).readlines()):  # Allow empty last line
                self.warnings.append({
                    "line": line_num,
                    "type": "empty_line",
                    "message": "Empty line found"
                })
            return
        
        # 1. JSON Structure Validation
        try:
            data = json.loads(line)
        except json.JSONDecodeError as e:
            self.errors.append({
                "line": line_num,
                "type": "json_error",
                "message": f"Invalid JSON: {str(e)}"
            })
            return
        
        # 2. Schema Validation
        self._validate_schema(line_num, data)
        
        # 3. Content Validation
        if isinstance(data, dict):
            self._validate_content(line_num, data)
    
    def _validate_schema(self, line_num: int, data: Any) -> None:
        """Validate the JSON schema structure."""
        
        if not isinstance(data, dict):
            self.errors.append({
                "line": line_num,
                "type": "schema_error",
                "message": "Line must be a JSON object"
            })
            return
        
        # Required fields
        required_fields = {"instruction", "input", "output"}
        missing_fields = required_fields - set(data.keys())
        
        if missing_fields:
            self.errors.append({
                "line": line_num,
                "type": "schema_error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            })
        
        # Check for unexpected fields
        unexpected_fields = set(data.keys()) - required_fields
        if unexpected_fields:
            self.warnings.append({
                "line": line_num,
                "type": "schema_warning",
                "message": f"Unexpected fields found: {', '.join(unexpected_fields)}"
            })
        
        # Validate field types
        for field in required_fields:
            if field in data and not isinstance(data[field], str):
                self.errors.append({
                    "line": line_num,
                    "type": "schema_error",
                    "message": f"Field '{field}' must be a string, got {type(data[field]).__name__}"
                })
    
    def _validate_content(self, line_num: int, data: Dict[str, str]) -> None:
        """Validate the content quality and consistency."""
        
        # Check for empty fields
        for field in ["instruction", "input", "output"]:
            if field in data:
                if not data[field].strip():
                    self.errors.append({
                        "line": line_num,
                        "type": "content_error",
                        "message": f"Field '{field}' cannot be empty"
                    })
                elif len(data[field].strip()) < 5:
                    self.warnings.append({
                        "line": line_num,
                        "type": "content_warning",
                        "message": f"Field '{field}' seems very short (< 5 characters)"
                    })
        
        # Validate output code if present
        if "output" in data and data["output"].strip():
            # Static validation first (fast)
            static_valid = self._validate_cadquery_code_static(line_num, data["output"])
            
            # Dynamic validation only if static passes (slower but thorough)
            if static_valid and self.enable_dynamic_validation:
                self._validate_cadquery_code_dynamic(line_num, data["output"])
        
        # Validate instruction-input-output consistency
        if all(field in data for field in ["instruction", "input", "output"]):
            self._validate_consistency(line_num, data)
    
    def _validate_cadquery_code_static(self, line_num: int, code: str) -> bool:
        """Static validation of CadQuery code syntax and structure."""
        initial_error_count = len(self.errors)
        
        # 1. Python syntax validation
        try:
            ast.parse(code)
        except SyntaxError as e:
            self.errors.append({
                "line": line_num,
                "type": "syntax_error",
                "message": f"Python syntax error: {str(e)}"
            })
            return
        
        # 2. Required import validation
        if "import cadquery as cq" not in code:
            self.errors.append({
                "line": line_num,
                "type": "import_error",
                "message": "Missing required import: 'import cadquery as cq'"
            })
        
        # 3. Result variable validation
        if "result = " not in code:
            self.errors.append({
                "line": line_num,
                "type": "structure_error",
                "message": "Missing 'result = ' assignment"
            })
        
        # 4. CadQuery pattern validation
        if not re.search(r'cq\.Workplane\(["\']X[YZ]["\']|["\'][YZ]X["\']|["\'][YZ][XZ]["\']\)', code):
            self.warnings.append({
                "line": line_num,
                "type": "pattern_warning",
                "message": "No standard CadQuery Workplane pattern found"
            })
        
        # 5. Validate numeric parameters
        self._validate_numeric_parameters(line_num, code)
        
        return len(self.errors) == initial_error_count
    
    def _validate_cadquery_code_dynamic(self, line_num: int, code: str) -> None:
        """Dynamic execution validation - actually runs CadQuery code to verify geometry."""
        
        try:
            # Create isolated execution environment
            local_scope = {}
            global_scope = {'cq': cq}
            
            # Execute the code
            exec(code, global_scope, local_scope)
            
            # Check if result was created
            result_obj = local_scope.get('result')
            if result_obj is None:
                self.errors.append({
                    "line": line_num,
                    "type": "execution_error",
                    "message": "Code executed but 'result' variable was not created"
                })
                return
            
            # Validate result type
            if not isinstance(result_obj, (cq.Workplane, cq.Shape)):
                self.errors.append({
                    "line": line_num,
                    "type": "execution_error",
                    "message": f"Result is not a valid CadQuery object, got {type(result_obj).__name__}"
                })
                return
            
            # Try to export to STL - the ultimate validation test
            temp_stl_path = os.path.join(self.temp_dir, f"test_line_{line_num}.stl")
            
            try:
                cq.exporters.export(result_obj, temp_stl_path)
                
                # Verify the exported file exists and has reasonable size
                if os.path.exists(temp_stl_path):
                    file_size = os.path.getsize(temp_stl_path)
                    if file_size < 100:  # STL files should be at least 100 bytes
                        self.warnings.append({
                            "line": line_num,
                            "type": "geometry_warning",
                            "message": f"Generated STL is very small ({file_size} bytes) - may be degenerate geometry"
                        })
                    
                    # Clean up the test file
                    os.remove(temp_stl_path)
                else:
                    self.errors.append({
                        "line": line_num,
                        "type": "export_error",
                        "message": "STL export completed but file was not created"
                    })
                    
            except Exception as export_error:
                self.errors.append({
                    "line": line_num,
                    "type": "geometry_error",
                    "message": f"Geometry export failed: {str(export_error)}"
                })
                
        except Exception as e:
            self.errors.append({
                "line": line_num,
                "type": "runtime_error",
                "message": f"Code execution failed: {str(e)}"
            })
    
    def _validate_numeric_parameters(self, line_num: int, code: str) -> None:
        """Validate that numeric parameters in CadQuery code are reasonable."""
        
        # Find function calls with numeric parameters
        numeric_functions = [
            'box', 'cylinder', 'sphere', 'hole', 'fillet', 'chamfer',
            'translate', 'rotate', 'rarray', 'polarArray', 'cboreHole'
        ]
        
        for func in numeric_functions:
            # Look for function calls
            pattern = rf'{func}\s*\([^)]*\)'
            matches = re.finditer(pattern, code)
            
            for match in matches:
                func_call = match.group()
                # Extract numeric values
                numbers = re.findall(r'-?\d+(?:\.\d+)?', func_call)
                
                for num_str in numbers:
                    try:
                        num = float(num_str)
                        # Enhanced parameter validation
                        if func in ['box', 'cylinder', 'sphere'] and num <= 0:
                            self.errors.append({
                                "line": line_num,
                                "type": "parameter_error",
                                "message": f"Dimension parameter {num} should be positive in {func}()"
                            })
                        elif func in ['box', 'cylinder', 'sphere'] and num > 1000:
                            self.warnings.append({
                                "line": line_num,
                                "type": "parameter_warning",
                                "message": f"Large dimension parameter {num} in {func}() - verify units"
                            })
                        elif func in ['fillet', 'chamfer'] and num <= 0:
                            self.errors.append({
                                "line": line_num,
                                "type": "parameter_error",
                                "message": f"Fillet/chamfer radius {num} must be positive"
                            })
                        elif func in ['hole'] and num <= 0:
                            self.errors.append({
                                "line": line_num,
                                "type": "parameter_error",
                                "message": f"Hole diameter {num} must be positive"
                            })
                    except ValueError:
                        continue
    
    def _validate_consistency(self, line_num: int, data: Dict[str, str]) -> None:
        """Validate consistency between instruction, input, and output."""
        
        instruction = data["instruction"].lower()
        input_text = data["input"].lower()
        output = data["output"].lower()
        
        # Enhanced dimension validation with diameter/radius conversion
        dimension_pattern = r'(\d+(?:\.\d+)?)\s*mm'
        input_dimensions = re.findall(dimension_pattern, input_text)
        output_dimensions = re.findall(r'(\d+(?:\.\d+)?)', output)
        
        # Check for diameter/radius conversions
        for dim in input_dimensions:
            dim_float = float(dim)
            radius_equivalent = str(dim_float / 2)
            
            if dim not in output_dimensions and radius_equivalent not in output_dimensions:
                # Check if it's a diameter->radius conversion
                if "diameter" in input_text and radius_equivalent in output_dimensions:
                    # This is correct - diameter converted to radius
                    continue
                else:
                    self.warnings.append({
                        "line": line_num,
                        "type": "consistency_warning",
                        "message": f"Dimension {dim}mm from input not found in output"
                    })
        
        # Enhanced shape consistency validation
        shape_keywords = {
            'box': ['box', 'cube', 'rectangular', 'square', 'plate'],
            'cylinder': ['cylinder', 'rod', 'pipe', 'circular'],
            'sphere': ['sphere', 'ball'],
            'wedge': ['wedge', 'triangular']
        }
        
        detected_shapes = []
        for shape, keywords in shape_keywords.items():
            if any(keyword in input_text for keyword in keywords):
                detected_shapes.append(shape)
        
        for shape in detected_shapes:
            if f'.{shape}(' not in output:
                self.warnings.append({
                    "line": line_num,
                    "type": "consistency_warning",
                    "message": f"Input mentions {shape} but output doesn't use .{shape}()"
                })
    
    def print_report(self) -> None:
        """Print a detailed validation report."""
        
        print("\n" + "="*60)
        print("DATASET VALIDATION REPORT")
        print("="*60)
        
        total_lines = sum(1 for line in open(self.dataset_path) if line.strip())
        print(f"Total lines processed: {total_lines}")
        print(f"Dynamic validation: {'ENABLED' if self.enable_dynamic_validation else 'DISABLED'}")
        print(f"Errors found: {len(self.errors)}")
        print(f"Warnings found: {len(self.warnings)}")
        
        # Categorize errors and warnings
        error_types = {}
        warning_types = {}
        
        for error in self.errors:
            error_type = error['type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        for warning in self.warnings:
            warning_type = warning['type']
            warning_types[warning_type] = warning_types.get(warning_type, 0) + 1
        
        if self.errors:
            print("\nERRORS (must be fixed):")
            print("-" * 40)
            for error in self.errors:
                print(f"Line {error['line']:3d}: [{error['type']}] {error['message']}")
            
            print(f"\nError Summary:")
            for error_type, count in error_types.items():
                print(f"- {error_type}: {count} occurrences")
        
        if self.warnings:
            print("\nWARNINGS (should be reviewed):")
            print("-" * 40)
            for warning in self.warnings:
                print(f"Line {warning['line']:3d}: [{warning['type']}] {warning['message']}")
            
            print(f"\nWarning Summary:")
            for warning_type, count in warning_types.items():
                print(f"- {warning_type}: {count} occurrences")
        
        # Enhanced status reporting
        if not self.errors and not self.warnings:
            print("\nDATASET VALIDATION PASSED! All validations successful.")
            print("JSON structure: VALID")
            print("Content quality: EXCELLENT") 
            print("Code syntax: VALID")
            if self.enable_dynamic_validation:
                print("Geometry generation: ALL SUCCESSFUL")
                print("STL export: ALL SUCCESSFUL")
            print("Ready for production training!")
        elif not self.errors:
            print(f"\nDATASET READY! No critical errors found.")
            if self.enable_dynamic_validation:
                print("All code executes successfully and generates valid geometry")
            print(f"Please review {len(self.warnings)} warnings for optimization")
        else:
            print(f"\nVALIDATION FAILED! Please fix {len(self.errors)} critical errors.")
            print("Consider using the automatic fixer: python3 src/fix_dataset.py")
        
        print("="*60)


def main():
    """Main validation function."""
    
    # Default dataset path
    dataset_path = "data/dataset.jsonl"
    enable_dynamic = True
    
    # Parse command line arguments
    args = sys.argv[1:]
    if args:
        if '--static-only' in args:
            enable_dynamic = False
            args.remove('--static-only')
        if args:
            dataset_path = args[0]
    
    validator = DatasetValidator(dataset_path, enable_dynamic)
    is_valid, errors, warnings = validator.validate()
    validator.print_report()
    
    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
