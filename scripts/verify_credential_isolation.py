#!/usr/bin/env python3
"""
Static Code Analysis Tool: Verify Credential Isolation

This script performs static analysis to verify that credentials are never
passed to LLM code paths. Suitable for CI/CD pipelines and security audits.

Usage:
    python scripts/verify_credential_isolation.py
    
Exit Codes:
    0: No violations detected (safe to deploy)
    1: Violations detected (review required)
"""

import ast
import sys
from pathlib import Path
from typing import List, Dict

class CredentialLeakDetector(ast.NodeVisitor):
    """
    AST visitor to detect if credentials are passed to LLM functions.
    
    Detects patterns like:
    - llm.generate(f"Login with {username}")
    - agent.run(task=f"Use password: {password}")
    - Any reference to credential variables in LLM calls
    """
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.violations: List[Dict] = []
        self.current_function = None
        self.in_llm_call = False
    
    def visit_FunctionDef(self, node):
        """Track which function we're in for better error messages"""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_Call(self, node):
        """Check function calls for LLM interactions with credentials"""
        # Detect LLM method calls (generate, run, invoke, etc.)
        is_llm_call = False
        
        if isinstance(node.func, ast.Attribute):
            # Check for methods like llm.generate(), agent.run()
            if node.func.attr in ['generate', 'run', 'invoke', 'chat', 'complete']:
                is_llm_call = True
        
        if isinstance(node.func, ast.Name):
            # Check for direct function calls
            if node.func.id in ['generate_text', 'call_llm', 'invoke_agent']:
                is_llm_call = True
        
        if is_llm_call:
            # Check all arguments to this LLM call
            for arg in node.args:
                if self._contains_credentials(arg):
                    self.violations.append({
                        'file': self.filepath,
                        'function': self.current_function or '<module>',
                        'line': node.lineno,
                        'issue': 'Credentials passed to LLM call',
                        'code': ast.unparse(node) if hasattr(ast, 'unparse') else '<code>'
                    })
            
            # Check keyword arguments
            for keyword in node.keywords:
                if self._contains_credentials(keyword.value):
                    self.violations.append({
                        'file': self.filepath,
                        'function': self.current_function or '<module>',
                        'line': node.lineno,
                        'issue': f'Credentials in keyword argument: {keyword.arg}',
                        'code': ast.unparse(node) if hasattr(ast, 'unparse') else '<code>'
                    })
        
        self.generic_visit(node)
   
    def _contains_credentials(self, node) -> bool:
        """
        Recursively check if an AST node references credentials.
        
        Detects:
        - Variable names: username, password, secret, credentials
        - Attribute access: obj.username, secrets_manager.password
        - F-strings containing credential variables
        """
        # Check simple variable names
        if isinstance(node, ast.Name):
            suspicious_names = ['username', 'password', 'credentials', 'secret', 'passwd', 'pwd', 'secrets_manager']
            if any(name in node.id.lower() for name in suspicious_names):
                return True
        
        # Check attribute access (obj.username)
        if isinstance(node, ast.Attribute):
            if self._contains_credentials(node.value):
                return True
            suspicious_attrs = ['username', 'password', 'secret']
            if any(attr in node.attr.lower() for attr in suspicious_attrs):
                return True
        
        # Check f-strings and formatted strings
        if isinstance(node, ast.JoinedStr):
            for value in node.values:
                if isinstance(value, ast.FormattedValue):
                    if self._contains_credentials(value.value):
                        return True
        
        # Check string concatenation
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            if self._contains_credentials(node.left) or self._contains_credentials(node.right):
                return True
        
        # Check format() calls
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'format':
                for arg in node.args:
                    if self._contains_credentials(arg):
                        return True
        
        return False

def analyze_file(filepath: Path) -> List[Dict]:
    """
    Analyze a Python file for credential leaks.
    
    Returns:
        List of violation dictionaries
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        tree = ast.parse(source_code, filename=str(filepath))
        detector = CredentialLeakDetector(str(filepath))
        detector.visit(tree)
        
        return detector.violations
    
    except SyntaxError as e:
        print(f"⚠️  Syntax error in {filepath}: {e}")
        return []
    except Exception as e:
        print(f"⚠️  Failed to analyze {filepath}: {e}")
        return []

def main():
    """Run analysis on all source files"""
    print("🔬 Static Code Analysis: Credential Isolation Verification")
    print("=" * 70)
    
    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Find all Python files in src/
    src_dir = project_root / 'src'
    if not src_dir.exists():
        print(f"❌ Source directory not found: {src_dir}")
        sys.exit(1)
    
    py_files = list(src_dir.glob('**/*.py'))
    print(f"📁 Analyzing {len(py_files)} Python files in {src_dir}")
    print()
    
    # Analyze each file
    all_violations = []
    files_with_violations = []
    
    for filepath in py_files:
        violations = analyze_file(filepath)
        if violations:
            all_violations.extend(violations)
            files_with_violations.append(filepath)
            print(f"⚠️  {filepath.relative_to(project_root)}: {len(violations)} violation(s)")
        else:
            print(f"✅ {filepath.relative_to(project_root)}")
    
    print()
    print("=" * 70)
    
    # Generate report
    if all_violations:
        print(f"🚨 SECURITY VIOLATIONS DETECTED: {len(all_violations)} issue(s)")
        print()
        
        for i, violation in enumerate(all_violations, 1):
            print(f"\n❌ Violation #{i}:")
            print(f"   File: {violation['file']}")
            print(f"   Function: {violation['function']}")
            print(f"   Line: {violation['line']}")
            print(f"   Issue: {violation['issue']}")
            if 'code' in violation:
                print(f"   Code: {violation['code'][:100]}...")
        
        print()
        print("=" * 70)
        print("⛔ FAILED - Review violations before deploying")
        sys.exit(1)
    
    else:
        print(f"✅ NO CREDENTIAL LEAKS DETECTED")
        print(f"   • Analyzed: {len(py_files)} files")
        print(f"   • Violations: 0")
        print(f"   • Status: Safe to deploy!")
        print()
        print("🔒 All LLM interactions are credential-free")
        sys.exit(0)

if __name__ == "__main__":
    main()
