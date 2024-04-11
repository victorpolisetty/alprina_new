if test -d demo; then
  echo "Removing previous agent build"
  rm -r demo
fi

find . -empty -type d -delete  # remove empty directories to avoid wrong hashes
autonomy packages lock
autonomy fetch --local --agent author/demo && cd demo

cp $PWD/../ethereum_private_key.txt .
autonomy add-key ethereum ethereum_private_key.txt
autonomy issue-certificates
aea -s run