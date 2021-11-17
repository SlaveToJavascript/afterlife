docker build -t afterlife/orders:1.0.0 .
docker run -p 5001:5001 -e dbURL=mysql+mysqlconnector://is213@host.docker.internal:3306/order afterlife/orders:1.0.0