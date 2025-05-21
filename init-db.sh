#!/bin/bash
set -e

# -- Helpers --
command_exists() { command -v "$1" >/dev/null 2>&1; }

# -- 1. Install MongoDB Shell (mongosh) if missing --
if ! command_exists mongosh; then
  echo "Installing mongosh..."
  curl -fsSL https://pgp.mongodb.com/server-6.0.asc | gpg --dearmor \
    -o /usr/share/keyrings/mongodb-server-6.0.gpg

  echo "deb [signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg] \
    https://repo.mongodb.org/apt/debian bookworm/mongodb-org/6.0 main" \
    | tee /etc/apt/sources.list.d/mongodb-org-6.0.list

  apt-get update
  apt-get install -y mongodb-mongosh
else
  echo "mongosh already installed."
fi

# -- 2. Install mongoimport if missing --
if ! command_exists mongoimport; then
  echo "Installing mongoimport (database tools)..."
  apt-get update
  apt-get install -y mongodb-database-tools
else
  echo "mongoimport already installed."
fi

# -- 3. Wait for the remote MongoDB container --
echo "Waiting for MongoDB at 'mongodb:27017' to be ready..."
until mongosh "mongodb://mongodb:27017" --quiet \
      --eval "db.adminCommand('ping')" &>/dev/null; do
  echo "  still waiting..."
  sleep 2
done

echo "MongoDB is up! Importing data..."

# -- 4. Import your JSON collections --
IMPORT_DIR="/workspace/applicationDB/applicationDB"

for file in "$IMPORT_DIR"/*.json; do
  filename=$(basename "$file")
  db_name="${filename%%.*}"                # applicationDB
  collection_name="${filename#*.}"         # users.json
  collection_name="${collection_name%%.*}" # users
  echo "Importing $file into $db_name.$collection_name"
  mongoimport --uri="mongodb://mongodb:27017/$db_name" \
    --collection="$collection_name" \
    --file="$file" \
    --jsonArray --drop
done

echo "DB Import complete."