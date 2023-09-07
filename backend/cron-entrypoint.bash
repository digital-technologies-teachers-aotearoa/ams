#!/bin/bash
printenv >> /etc/environment
echo "Starting cron"

tail -f /var/log/cron.log &
cron -f
