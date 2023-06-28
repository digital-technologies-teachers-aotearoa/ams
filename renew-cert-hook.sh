#/bin/bash
cd /opt/dtta-ams
docker-compose down
certbot certonly --standalone -d dtta-test.catalystdemo.net.nz -m dtta-ams-dev@catalyst.net.nz --agree-tos
docker-compose -f docker-compose.yml -f docker-compose.test.yml up -d