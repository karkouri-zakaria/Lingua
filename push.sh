#!/bin/bash

# Exit on error
set -e

echo "🧹 Removing old .git folder..."
rm -rf .git

echo "🔄 Reinitializing Git..."
git init

echo "📌 Renaming initial branch to 'main'..."
git branch -m main

echo "➕ Adding all files..."
git add .

echo "✅ Committing with message 'Lingua'..."
git commit -m "Lingua"

echo "🔗 Adding remote origin..."
git remote add origin "https://github.com/karkouri-zakaria/Lingua.git"

echo "📤 Force pushing only 'main' branch..."
git push -f origin main

echo "✅ Done. 'main' branch was force-pushed."
