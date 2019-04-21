#!/bin/bash

COOKIE="${1}"
QR_CODE="${2}"

STATUS_CODE=$(echo "${QR_CODE}" | curl -s -o /dev/null -w "%{http_code}" -H "Cookie: sessionid=${COOKIE}" -F 'text=<-' 'http://localhost:8000/receipts/add/')

if [[ "${STATUS_CODE}" != 302 ]]; then
    echo "Cannot add ${QR_CODE}, status is ${STATUS_CODE}"
fi
