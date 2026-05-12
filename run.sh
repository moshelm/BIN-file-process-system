#!/bin/bash

# הגדרת הכתובת והפורט של ממשק המשתמש
UI_URL="http://localhost:8000"
MAX_WAIT=30
COUNTER=0

echo "🚀 Starting Docker Compose services..."
docker compose up -d --build

echo "⏳ Waiting up to ${MAX_WAIT} seconds for Flet UI at $UI_URL..."

# לולאה שבודקת את השרת, אבל עוצרת אחרי MAX_WAIT שניות
while ! curl -s -f -o /dev/null "$UI_URL"
do
  sleep 1
  echo -n "."
  COUNTER=$((COUNTER+1))
  
  if [ $COUNTER -ge $MAX_WAIT ]; then
    echo -e "\n❌ Failed: Flet UI did not respond within 30 seconds."
    echo "💡 Tip: Check logs with 'docker compose logs flet-app'"
    exit 1 # יציאה עם קוד שגיאה כדי לעצור את הסקריפט
  fi
done

echo -e "\n✅ Flet UI is up and running!"
echo "🌐 Opening browser..."

# פתיחת הדפדפן בהתאם למערכת ההפעלה
if which xdg-open > /dev/null; then
  xdg-open "$UI_URL"
elif which open > /dev/null; then
  open "$UI_URL"
elif which start > /dev/null; then
  start "$UI_URL"
else
  echo "⚠️ Could not detect the web browser. Please open manually: $UI_URL"
fi