# Remove all migration Python files except __init__.py
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete

# Remove all compiled Python files in migrations directories
find . -path "*/migrations/*.pyc" -delete

# Remove all __pycache__ directories within migrations
find . -path "*/migrations/__pycache__" -type d -exec rm -rf {} +

# Delete the SQLite database file
rm core/db.sqlite3