FROM python:3
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ./supplier_reply.py . 
CMD [ "python", "./supplier_reply.py" ]