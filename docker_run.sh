#!/bin/bash
docker rm -f webmonitorplus
# rm db/db.sqlite3
docker run -it --name webmonitorplus -v /root/WebMonitorPlus:/app  -p 8886:5000 docker.io/library/webmonitorplus