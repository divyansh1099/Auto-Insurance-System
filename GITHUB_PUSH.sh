#!/bin/bash
# Script to push project to GitHub

echo "🚀 Preparing to push to GitHub..."
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "⚠️  Git not initialized. Run: git init"
    exit 1
fi

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 Staging all changes..."
    git add .
    
    echo "💾 Committing changes..."
    git commit -m "Reorganize project structure and prepare for GitHub

- Reorganized into src/, docs/, bin/, models/, data/ structure
- Removed unnecessary files and large data directories
- Updated docker-compose.yml paths
- Created comprehensive README.md
- Updated .gitignore for clean repository"
    
    echo "✅ Changes committed!"
else
    echo "✅ No changes to commit"
fi

# Check if remote exists
if git remote | grep -q origin; then
    echo "📤 Pushing to GitHub..."
    git push -u origin main || git push -u origin master
    echo "✅ Push complete!"
else
    echo "⚠️  No remote configured."
    echo "Run: git remote add origin <your-repo-url>"
    echo "Then run this script again"
fi

