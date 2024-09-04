if test -d alprina_agent; then
  echo "Removing previous agent build"
  rm -r alprina_agent
fi

find . -empty -type d -delete  # remove empty directories to avoid wrong hashes
autonomy packages lock
autonomy fetch --local --agent victorpolisetty/alprina_agent && cd alprina_agent

cp $PWD/../ethereum_private_key.txt .
autonomy add-key ethereum ethereum_private_key.txt
autonomy issue-certificates
# aea -s -v DEBUG run
aea -s run