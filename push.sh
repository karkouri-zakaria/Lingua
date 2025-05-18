#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Navigate to the parent directory
cd ..

# Define the directory where your project resides
PROJECT_DIR="./app"

# Change to the project directory
cd "$PROJECT_DIR" || { echo "Directory $PROJECT_DIR not found."; exit 1; }

# Define the remote repository URL
REMOTE_URL="https://github.com/karkouri-zakaria/Lingua.git"

# Remove existing .git directory if it exists
if [ -d ".git" ]; then
    rm -rf .git
    echo "Removed existing .git directory."
fi

# Initialize a new Git repository
git init
echo "Initialized a new Git repository."

# Add the remote origin
git remote add origin "$REMOTE_URL"
echo "Added remote origin: $REMOTE_URL"

# Add all files to the staging area
git add .
echo "Staged all files for commit."

# Commit the changes
git commit -m "Lingua app"
echo "Committed changes."

# Set the branch name to main
git branch -M main
echo "Renamed branch to main."

# Force push to the remote repository
git push -f origin main
echo "Force pushed to origin main."
