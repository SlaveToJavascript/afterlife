FROM python:3
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ./twilio_sms.py . 
CMD [ "python", "./twilio_sms.py" ]