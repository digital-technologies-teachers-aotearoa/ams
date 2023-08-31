#!/bin/bash
set -e

cp ./frontend/css/main.min.css ./backend/ams/base/static/css/base.min.css
cp ./frontend/css/main.css ./backend/ams/base/static/css/base.css
cp -r ./frontend/js ./backend/ams/base/static/
cp -r ./frontend/fonts ./backend/ams/base/static/
cp -r ./frontend/images ./backend/ams/dtta/static/