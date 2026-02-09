import os
import re

# 📜 CONSTITUTION RULES
RULES = {
    # RULE 1: SYNTAX STRICTNESS
    "SYNTAX_ASYNC": {
        "pattern": r"try:\s*await.*except",
        "message": "❌ VIOLATION: Single-line 'try: await' detected. Use multi-line blocks for stability.",
        "type": "Critical"
    },
    
    # RULE 2: VACUUM PROTOCOL
    "VACUUM_SELECTOR": {
        "pattern": r"\.locator\(ur?['\"](div\.|span\.|td\.|tr\.)",
        "message": "⚠️ WARNING: Specific CSS selector detected (div/span/td/tr). Use 'Vacuum Mode' (grab all links/text) instead.",
        "type": "Warning"
    },
    
    # RULE 3: PREDICTIVE DORKING
    "DORK_QUESTION": {
        "pattern": r'search\?q=["\']Who is',
        "message": "❌ VIOLATION: Question-based query detected. Use Answer-Based Dorking.",
        "type": "Critical"
    }
}

EXCLUDES = ["verify_constitution.py", ".venv", ".git", "build", "dist", "__pycache__"]

def scan_file(filepath):
    issues = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
            for rule_name, rule_def in RULES.items():
                if re.search(rule_def["pattern"], line):
                    issues.append({
                        "file": filepath,
                        "line": i + 1,
                        "type": rule_def["type"],
                        "message": rule_def["message"],
                        "code": line.strip()
                    })
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        
    return issues

def main():
    print("🛡️ ANTIGRAVITY CONSTITUTION ENFORCER v1.0")
    print("=========================================")
    print("Scanning codebase for violations...\n")
    
    all_issues = []
    
    for root, dirs, files in os.walk("."):
        # Filter exclusions
        dirs[:] = [d for d in dirs if d not in EXCLUDES]
        
        for file in files:
            if file.endswith(".py") and file not in EXCLUDES:
                path = os.path.join(root, file)
                all_issues.extend(scan_file(path))

    if not all_issues:
        print("✅ CLEAN. No Constitution violations found.")
        print("   -> Nordic Transformation: ENABLED")
        print("   -> Vacuum Protocol: ACTIVE")
    else:
        print(f"⚠️ FOUND {len(all_issues)} VIOLATIONS:\n")
        for issue in all_issues:
            icon = "🔴" if issue["type"] == "Critical" else "🟡"
            print(f"{icon} [{issue['type']}] {issue['file']}:{issue['line']}")
            print(f"   {issue['message']}")
            print(f"   Code: {issue['code']}\n")
            
        print("ACTION REQUIRED: Fix these violations immediately.")

if __name__ == "__main__":
    main()
