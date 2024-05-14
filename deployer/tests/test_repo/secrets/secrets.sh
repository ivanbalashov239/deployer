#!/usr/bin/env bash
force=0
inputdir=$2
usage="Usage: $0 [-f|--force] <inputdir>"
case "$1" in
    -f|--force)
			force=1
      if [[ -d $2 ]] ; then
          inputdir=$2
      else
          echo $usage
          exit 1
      fi
    ;;
    -h|--help)
        echo $usage
    ;;
    *)
			force=0
      if [[ -d $1 ]] ; then
          inputdir=$1
      else
          echo $usage
          exit 1
      fi
    ;;
esac



lines=$(nix eval --no-net  --impure  --json  --expr "import ./secrets.nix" | jq -r "keys[]")
while IFS= read -r line; do
    created=0
    if [[ -e "./$line" ]] ; then
        created=1
    fi
    if (( created == 1 )); then
        if (( force == 1 ));  then
            echo "$inputdir/${line%".age"} > $line"
            mkdir -p $(dirname $line)
            cat $inputdir/${line%".age"} | ragenix --editor - --edit $line
        else
            echo "$line already created"
        fi
    elif (( created == 0 )); then
        echo "$inputdir/${line%".age"} > $line"
        mkdir -p $(dirname $line)
        cat $inputdir/${line%".age"} | ragenix --editor - --edit $line
    fi
done <<< "$lines"



exit 0
