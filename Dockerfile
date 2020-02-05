FROM python:3.7-alpine

COPY github_actions.py /github_actions.py
COPY bump_version.py /bump_version.py

ENTRYPOINT ["python", "/bump_version.py"]
