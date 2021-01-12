#!/bin/bash

source ./scripts/defaults.sh

cat << EOF
apiVersion: v1
data:
  BUCKET: `echo -n $BUCKET | base64 -w 0`
  BUCKET_GCE_KEY: `echo -n $BUCKET_GCE_KEY | base64 -w 0`
kind: Secret
metadata:
  name: covidimaging-backend-$TIER-bucket
  namespace: covidimaging-backend-$TIER
type: Opaque
EOF
