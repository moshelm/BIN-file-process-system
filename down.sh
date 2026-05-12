#!/bin/bash

echo "🛑 Stopping and removing Docker Compose services..."

# מוריד את הקונטיינרים, מוחק את הרשתות שלהם, אבל משאיר את ה-Volumes (אם יש)
docker compose down

echo "✅ All services successfully stopped and removed."