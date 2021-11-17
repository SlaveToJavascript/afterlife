Name of Project: AfterLife
Undertakers of Project: G1T3

Steps to deploy your HTML webpage to the docker container:
1. Create a Directory for the Website. Ensure that you have your HTML files already in the current directory.
2. Create a file called Dockerfile and place the following contents into the Dockerfile:

FROM nginx:alpine
COPY . /usr/share/nginx/html

These lines of code represent the image we're going to use along with copying the contents of the current directory into the container.

3. Build the Docker Image for the HTML Server by running the following command:

docker build -t html-server-image:v1 .

4. Run the Docker Container.
Run the following command to run the HTML container server:

docker run -d -p 80:80 html-server-image:v1

5. Test the Port with cURL.
Run the following command to ensure the server is running:

curl localhost:80

You can also view it in the browser now by accessing localhost:80