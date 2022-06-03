FROM python:3.8
WORKDIR /app
RUN pip install fastapi==0.78.0 uvicorn==0.17.6 elasticsearch==8.2.0 bert-serving-client==1.10.0 sentencepiece==0.1.96 slackweb==1.0.5
ENTRYPOINT [ "python3", "main.py" ]