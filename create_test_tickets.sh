#!/bin/bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2ZWFhZTUxYi00NmVmLTQ3ZmMtOWJlOS0wOTI0OGE4MzQ1ZmIiLCJyb2xlIjoiYWRtaW4iLCJ0eXBlIjoiYWNjZXNzIiwiaWF0IjoxNzg5NjM1ODkzLCJleHAiOjE3ODk2Mzc2OTN9.qjskwHmFnWGEtUKdsWVJyIy1vVtQ3wuA_AbLNhHXnmw"

for i in $(seq 1 25)
do
  curl -s -X POST http://localhost:8000/tickets \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"Test ticket number $i\",\"description\":\"This is sample bug report number $i for testing pagination\"}" \
    -o /dev/null
  echo "Created ticket $i"
done
