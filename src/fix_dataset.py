#!/usr/bin/env python3
"""
Dataset fixing utility for common issues in JSONL files.
Includes enhanced fixing capabilities and validation integration.
"""

import json
import re
import sys
import shutil
from pathlib import Path
from typing import List, Dict, Any


class DatasetFixer:
    def __init__(self, dataset_path: str):
        self.dataset_path = Path(dataset_path)
        self.backup_path = self.dataset_path.with_suffix('.jsonl.backup')
        
    def fix_common_issues(self, create_backup: bool = True) -> None:
        """Fix common issues in the dataset with enhanced checks."""
        
        if create_backup:
            self._create_backup()
        
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        changes_made = 0
        empty_lines_removed = 0
        
        for line_num, line in enumerate(lines, 1):
            original_line = line
            fixed_line = self._fix_line(line.strip())
            
            if not fixed_line and original_line.strip():
                empty_lines_removed += 1
                print(f"Removed invalid/empty line {line_num}")
                continue
            elif not fixed_line:
                # Skip empty lines
                continue
            
            if fixed_line != original_line.strip():
                changes_made += 1
                print(f"Fixed line {line_num}")
            
            if fixed_line:  # Only add non-empty lines
                fixed_lines.append(fixed_line + '\n')
        
        # Write fixed dataset
        with open(self.dataset_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        
        print(f"Dataset fixing complete.")
        print(f"Changes made: {changes_made}")
        print(f"Empty/invalid lines removed: {empty_lines_removed}")
        if create_backup:
            print(f"Original backed up to: {self.backup_path}")
    
    def _create_backup(self) -> None:
        """Create a backup of the original dataset."""
        shutil.copy2(self.dataset_path, self.backup_path)
        print(f"Backup created: {self.backup_path}")
    
    def _fix_line(self, line: str) -> str:
        """Fix common issues in a single line."""
        
        if not line:
            return ""
        
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            print(f"Skipping invalid JSON line: {line[:50]}...")
            return ""
        
        if not isinstance(data, dict):
            return ""
        
        # Fix missing fields
        required_fields = {"instruction", "input", "output"}
        if not all(field in data for field in required_fields):
            return ""
        
        # Clean up code formatting
        if "output" in data:
            data["output"] = self._fix_code_formatting(data["output"])
        
        # Ensure proper string formatting
        for field in ["instruction", "input", "output"]:
            if field in data:
                data[field] = data[field].strip()
        
        return json.dumps(data, ensure_ascii=False)
    
    def _fix_code_formatting(self, code: str) -> str:
        """Enhanced code formatting fixes for CadQuery code."""
        
        # Ensure proper import
        if "import cadquery as cq" not in code and "cq." in code:
            code = "import cadquery as cq\n\n" + code
        
        # Fix spacing around operators
        code = re.sub(r'(\w)\s*=\s*(\w)', r'\1 = \2', code)
        
        # Ensure result assignment
        if "result = " not in code and code.strip().startswith("cq."):
            code = "result = " + code
        
        # Fix common CadQuery method chaining formatting
        # Ensure proper line breaks for method chaining
        if ".faces(" in code and ".workplane(" in code:
            code = re.sub(r'(\)\s*)\.', r')\n    .', code)
        
        # Fix common parameter formatting issues
        code = re.sub(r'(\d+)\s*,\s*(\d+)', r'\1, \2', code)  # Fix spacing in parameters
        
        # Ensure proper indentation for multi-line statements
        lines = code.split('\n')
        formatted_lines = []
        for i, line in enumerate(lines):
            if i > 0 and line.strip().startswith('.') and not line.startswith('    '):
                formatted_lines.append('    ' + line.strip())
            else:
                formatted_lines.append(line)
        code = '\n'.join(formatted_lines)
        

    
    def fix_specific_issues(self, issue_types: List[str]) -> None:
        """Fix specific types of issues based on validation results."""
        
        print(f"Fixing specific issues: {', '.join(issue_types)}")
        
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        changes_made = 0
        
        for line_num, line in enumerate(lines, 1):
            original_line = line.strip()
            if not original_line:
                continue
                
            try:
                data = json.loads(original_line)
                fixed_data = self._fix_specific_data_issues(data, issue_types)
                
                fixed_line = json.dumps(fixed_data, ensure_ascii=False)
                if fixed_line != original_line:
                    changes_made += 1
                    print(f"Fixed specific issues on line {line_num}")
                
                fixed_lines.append(fixed_line + '\n')
                
            except json.JSONDecodeError:
                # Skip invalid JSON lines
                continue
        
        # Write fixed dataset
        with open(self.dataset_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        
        print(f"Specific issue fixing complete. Changes made: {changes_made}")
    
    def _fix_specific_data_issues(self, data: Dict[str, Any], issue_types: List[str]) -> Dict[str, Any]:
        """Fix specific data issues based on issue types."""
        
        if "consistency_warning" in issue_types:
            # Fix diameter/radius consistency issues
            if "output" in data and "input" in data:
                input_text = data["input"].lower()
                output_code = data["output"]
                
                # Look for diameter mentions and ensure radius conversion is clear
                if "diameter" in input_text:
                    # Add comment to clarify diameter->radius conversion
                    diameter_match = re.search(r'(\d+(?:\.\d+)?)\s*mm.*diameter', input_text)
                    if diameter_match:
                        diameter = float(diameter_match.group(1))
                        radius = diameter / 2
                        if str(radius) in output_code and "# Diameter" not in output_code:
                            # Add clarifying comment
                            output_code = output_code.replace(
                                f"cylinder({radius}",
                                f"cylinder({radius}  # Diameter {diameter}mm = radius {radius}mm"
                            )
                            data["output"] = output_code
        
        if "parameter_error" in issue_types:
            # Fix negative or zero parameters
            if "output" in data:
                output_code = data["output"]
                # This would require more complex parsing to fix automatically
                # For now, just flag for manual review
                pass
        
        return data

    def validate_after_fix(self, enable_dynamic: bool = True) -> None:
        """Run validation after fixing to show results."""
        print("\n" + "="*50)
        print("RUNNING VALIDATION AFTER FIXES")
        print("="*50)
        
        # Import and run validator
        try:
            from validate_dataset import DatasetValidator
            validator = DatasetValidator(str(self.dataset_path), enable_dynamic)
            is_valid, errors, warnings = validator.validate()
            validator.print_report()
        except ImportError:
            print("Could not import validator. Please run validation manually:")
            print(f"python3 src/validate_dataset.py {self.dataset_path}")


def main():
    """Enhanced main fixing function."""
    
    dataset_path = "data/dataset.jsonl"
    specific_issues = []
    
    # Parse command line arguments
    args = sys.argv[1:]
    if args:
        if '--issues' in args:
            idx = args.index('--issues')
            if idx + 1 < len(args):
                specific_issues = args[idx + 1].split(',')
                args = args[:idx] + args[idx + 2:]
        if args:
            dataset_path = args[0]
    
    fixer = DatasetFixer(dataset_path)
    
    # Ask for confirmation before making changes
    print(f"DATASET FIXER")
    print("=" * 40)
    print(f"About to fix dataset: {dataset_path}")
    print("This will create a backup and modify the original file.")
    
    if specific_issues:
        print(f"Targeting specific issues: {', '.join(specific_issues)}")
    
    response = input("Continue? (y/N): ").lower().strip()
    if response not in ['y', 'yes']:
        print("Operation cancelled.")
        return
    
    if specific_issues:
        fixer.fix_specific_issues(specific_issues)
    else:
        fixer.fix_common_issues()
    
    fixer.validate_after_fix()


if __name__ == "__main__":
    main()
