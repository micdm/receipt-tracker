#!/bin/bash

SITE_ADDRESS="${1}"
COOKIE="${2}"
QR_CODE="${3}"

STATUS_CODE=$(echo "${QR_CODE}" | curl -s -o /dev/null -w "%{http_code}" -H "Cookie: sessionid=${COOKIE}" -F 'text=<-' "${SITE_ADDRESS}/receipts/add/")

if [[ "${STATUS_CODE}" != 302 ]]; then
    echo "Cannot add ${QR_CODE}, status is ${STATUS_CODE}"
fi
