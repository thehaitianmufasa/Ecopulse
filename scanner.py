import os

EXCLUDED_DIRS = {'venv', '__pycache__', '.git', '.idea', '.vscode'}

def scan_folder(root='.'):
    print(f"\n📁 Scanning Project Folder: {os.path.abspath(root)}\n")
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip excluded directories like 'venv'
        if any(excluded in dirpath.split(os.sep) for excluded in EXCLUDED_DIRS):
            continue

        print(f"📂 Directory: {dirpath}")
        if 'templates' in dirpath:
            print("   🔎 Flask template folder detected")
        if 'static' in dirpath:
            print("   🔎 Flask static folder detected")

        for file in filenames:
            full_path = os.path.join(dirpath, file)
            print(f"   📄 File: {file}")
            if file.endswith(('.html', '.css', '.js')) and 'templates' not in dirpath and 'static' not in dirpath:
                print("   ⚠️ Warning: Flask may not find this unless in '/templates' or '/static'")
        print("-" * 60)

if __name__ == "__main__":
    scan_folder()
