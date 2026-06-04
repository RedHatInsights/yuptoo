#cd /app-root/yuptoo
#pipenv install --dev --skip-lock
#pipenv graph
#pipenv lock
#pipenv requirements > requirements.txt
cd /app-root/yuptoo
uv sync --all-extras
uv tree
uv lock
uv export --format requirements-txt --no-hashes > requirements.txt
