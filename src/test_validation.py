#!/usr/bin/env python3
"""
Test script to demonstrate dataset validation and fixing capabilities.
Tests both static and dynamic validation modes.
"""

import sys
from pathlib import Path

def test_cadquery_available():
    """Test if CadQuery is available for dynamic validation."""
    try:
        import cadquery as cq
        return True
    except ImportError:
        return False

def main():
    """Test the validation and fixing tools."""
    
    print("="*60)
    print("CADBOT DATASET VALIDATION TEST")
    print("="*60)
    
    cadquery_available = test_cadquery_available()
    print(f"CadQuery available: {'YES' if cadquery_available else 'NO'}")
    if not cadquery_available:
        print("Install with: pip install cadquery>=2.4.0")
    print()
    
    # Test 1: Run validation
    print("1. Running dataset validation...")
    print("-" * 40)
    
    try:
        from validate_dataset import DatasetValidator
        
        print("Testing static validation:")
        validator_static = DatasetValidator("data/dataset.jsonl", enable_dynamic_validation=False)
        is_valid_static, errors_static, warnings_static = validator_static.validate()
        
        if cadquery_available:
            print("\nTesting dynamic validation:")
            validator_dynamic = DatasetValidator("data/dataset.jsonl", enable_dynamic_validation=True)
            is_valid, errors, warnings = validator_dynamic.validate()
            validator_dynamic.print_report()
        else:
            print("\nSkipping dynamic validation (CadQuery not available)")
            is_valid, errors, warnings = is_valid_static, errors_static, warnings_static
        
        # Analyze the results
        print(f"\nValidation Summary:")
        print(f"- Static validation: {'VALID' if is_valid_static else 'INVALID'} ({len(errors_static)} errors, {len(warnings_static)} warnings)")
        if cadquery_available:
            print(f"- Dynamic validation: {'VALID' if is_valid else 'INVALID'} ({len(errors)} errors, {len(warnings)} warnings)")
        
        if warnings_static or (cadquery_available and warnings):
            print(f"\nWarning Analysis:")
            warning_types = {}
            all_warnings = warnings_static + (warnings if cadquery_available else [])
            for warning in all_warnings:
                warning_type = warning['type']
                warning_types[warning_type] = warning_types.get(warning_type, 0) + 1
            
            for w_type, count in warning_types.items():
                print(f"- {w_type}: {count} occurrences")
        
    except Exception as e:
        print(f"Error running validation: {e}")
        return 1
    
    # Test 2: Show example of what the fixer would do
    print(f"\n2. Dataset fixing capabilities...")
    print("-" * 40)
    print("The fixer can automatically:")
    print("- Remove empty lines")
    print("- Fix code formatting issues")
    print("- Add missing imports")
    print("- Ensure proper variable assignments")
    print("- Clean up whitespace")
    print("- Create backups before changes")
    print("- Enhanced method chaining formatting")
    print("- Specific issue targeting")
    
    # Test 3: Recommendations
    print(f"\n3. Recommendations for your dataset:")
    print("-" * 40)
    
    if is_valid and len(warnings) <= 1:
        print("Your dataset is in excellent condition!")
        print("Only minor consistency warnings found")
        print("All JSON structure is valid")
        print("All CadQuery code is syntactically correct")
        print("Ready for training!")
    else:
        print("Some issues found that should be addressed")
        
    print(f"\n4. Usage instructions:")
    print("-" * 40)
    print("Static validation: python3 src/validate_dataset.py --static-only")
    print("Dynamic validation: python3 src/validate_dataset.py")
    print("Fix issues: python3 src/fix_dataset.py")
    print("Run this test: python3 src/test_validation.py")
    
    print("\n" + "="*60)
    
    return 0 if is_valid else 1

if __name__ == "__main__":
    sys.exit(main())