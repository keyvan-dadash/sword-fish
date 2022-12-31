#!/usr/bin/bash

mkdir -p build-configs

for i in "$@"; do
  IFS=$'\n'
  files=($(find "$i" -type f))
  unset IFS
  for j in "${files[@]}"
  do
    filename=$(basename -- "$j")
    extension="${filename##*.}"
    filename="${filename%.*}"
    echo "${i}-env/${filename}.env"
    export $(grep -v '^#' "${i}-env/${filename}.env" | xargs)

    if test -f "${i}-env/general-var.env"; then
      export $(grep -v '^#' "${i}-env/general-var.env" | xargs)
    fi

    ./env-filler.py --json-config "$j" --output-dir build-configs 

    unset $(grep -v '^#' "${i}-env/${filename}.env" | awk 'BEGIN { FS = "=" } ; { print $1 }')

    if test -f "${i}-env/general-var.env"; then
      unset $(grep -v '^#' "${i}-env/general-var.env" | awk 'BEGIN { FS = "=" } ; { print $1 }')
    fi

  done
done


