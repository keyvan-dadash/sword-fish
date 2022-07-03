#!/usr/bin/bash

for i in "$@"; do
  IFS=$'\n'
  files=($(find "$i" -type f))
  unset IFS
  for j in "${files[@]}"
  do
    filename=$(basename -- "$j")
    extension="${filename##*.}"
    filename="${filename%.*}"
    echo "env-files/${filename}.env"
    export $(grep -v '^#' "env-files/${filename}.env" | xargs)
    ./env-filler.py --json-config "$j" --output-dir build-configs
    unset $(grep -v '^#' "env-files/${filename}.env" | awk 'BEGIN { FS = "=" } ; { print $1 }')
  done
done


