#!/bin/bash
docker rm -f mywebmonitorplus
# rm db/db.sqlite3
docker run -it --name mywebmonitorplus -v /root/WebMonitorPlus:/app  -p 8886:5000 docker.io/library/mywebmonitorplus