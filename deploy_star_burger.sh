#!/bin/bash
set -e
source .env
echo "Check for updates on remote git repository."
git pull

echo "Install Python dependencies."
./venv/bin/pip install -r requirements.txt

echo "Collect Django static."
./venv/bin/python3 manage.py collectstatic --noinput

echo "Apply Django migrations."
./venv/bin/python3 manage.py migrate --noinput

echo "Restart systemd services."
systemctl restart star-burger.service
systemctl restart postgresql.service
systemctl reload nginx.service

echo "Send deployment info to Rollbar."
sha=$(git rev-parse HEAD)
curl --request POST \
     --url https://api.rollbar.com/api/1/deploy \
     --header "X-Rollbar-Access-Token: ${ROLLBAR_TOKEN}" \
     --header 'accept: application/json' \
     --header 'content-type: application/json' \
     --data '
              {
                "environment": "'development'",
                "local_username": "'"${USER}"'",
                "revision": "'"${sha}"'",
                "comment": "'"${comment}"'",
                "status": "succeeded"
              }
            '

echo "Deployment completed!"
