FROM python:latest

ADD requirements.txt requirements.txt
RUN pip install -r   requirements.txt

ADD mcp.py mcp.py

EXPOSE 8011

CMD ["python","-u","mcp.py"]
