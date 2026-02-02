import os

# 1. Soft Reset: Undo the last commit but keep the code changes (Waterfall logic)
print("↩️ Undoing last commit (Soft Reset)...")
os.system("git reset --soft HEAD~1")

# 2. Unstage the Giant Folders (dist/ and build/)
print("🧹 Removing large files from staging...")
os.system("git reset HEAD dist build")
os.system("git rm -r --cached dist build") 

# 3. Update .gitignore so they never get added again
print("🛡️ Updating .gitignore...")
with open(".gitignore", "a") as f:
    f.write("\n# Build Artifacts\ndist/\nbuild/\n*.exe\n*.pkg\n")

# 4. Re-Commit ONLY the code
print("💾 Committing clean code...")
os.system("git add .")
os.system("git commit -m 'Implemented Waterfall Logic (Clean build)'")

# 5. Push
print("🚀 Pushing to GitHub...")
os.system("git push")
