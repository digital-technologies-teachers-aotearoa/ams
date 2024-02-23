#!/bin/bash
printenv >> /etc/environment
echo "Starting cron"

mkfifo /tmp/cron.out
chmod 666 /tmp/cron.out

tail -f /tmp/cron.out &

cron -f
