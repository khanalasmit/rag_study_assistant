#Base image
FROM python:3.11-slim

#set working directory 
WORKDIR /app

#copy requirements
COPY requirements.txt .

#upgrade pip and install dependencies with extended timeout and retries
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --timeout=300 --retries=5 -r requirements.txt

#copying the entire application
COPY . .

#port 8000 for fastapi backend
#port 8051 for streamlit app

EXPOSE 8000 8051

#creating the startup script
RUN echo '#!/bin/bash\n\
cd /app/ && uvicorn main:app --host 0.0.0.0 --port 8000 &\n\
cd /app/frontend/ && streamlit run app.py --server.port 8051 --server.address 0.0.0.0\n\
'>/app/start.sh && chmod +x /app/start.sh

#command to run both backend and frontend
CMD ["/bin/bash","/app/start.sh"]


