sudo docker pull swaggerapi/swagger-codegen-cli-v3
sudo docker run --rm -v ${PWD}/query:/Downloads swaggerapi/swagger-codegen-cli-v3 generate \
     -i /Downloads/tpoisonooo-seed-1.0.0-resolved.json \
     -l python \
     -o /Downloads/python
