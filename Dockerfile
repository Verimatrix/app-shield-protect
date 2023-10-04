FROM python:3.8-slim

RUN apt-get update  && apt-get install jq -y

ADD cli /aps-cli

RUN pip install --no-cache-dir -r /aps-cli/requirements.txt

# Copies your code file from your action repository to the filesystem path `/` of the container
COPY entrypoint.sh /entrypoint.sh

# Executes `entrypoint.sh` when the Docker container starts up
ENTRYPOINT ["/entrypoint.sh"]
