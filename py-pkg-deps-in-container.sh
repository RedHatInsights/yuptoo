cd /app-root/yuptoo
pipenv install --dev --skip-lock
pipenv graph
pipenv lock
pipenv requirements > requirements.txt
