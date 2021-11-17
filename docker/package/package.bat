docker build -t afterlife/package:1.0.0 .
docker run -p 5000:5000 -e dbURL=mysql+mysqlconnector://is213@host.docker.internal:3306/package afterlife/package:1.0.0