#!/bin/bash

PGUSER=postgres

AIO_HOST=0.0.0.0
AIO_PORT=8081
APP_ID=app-covidimaging
AIDBOX_PORT=8080
AIDBOX_CLIENT_ID=root

case $TIER in
    master)
        AIDBOX_BASE_URL=https://master-backend.covidimaging.beda.software
        FRONTEND_URL=https://master.covidimaging.beda.software
        ;;
    staging)
        AIDBOX_BASE_URL=https://staging-backend.covidimaging.beda.software
        FRONTEND_URL=https://staging.covidimaging.beda.software
        ;;
    develop)
        AIDBOX_BASE_URL=https://develop-backend.covidimaging.beda.software
        FRONTEND_URL=https://develop.covidimaging.beda.software
        ;;
esac
