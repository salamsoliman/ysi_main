#!/bin/bash

BRANCH="master"
if [ $# -ge 2 ]; then 
   BRANCH="$1"
   shift 1
fi

for repo in dns-zone-file-py ysi-profiles-py virtualchain ysi-core ysi-files ysi-gpg; do
   git clone "https://github.com/ysi/$repo"
   pushd "$repo"
   git checkout "$BRANCH"
   python ./setup.py build && sudo python ./setup.py install

   if [ $? -ne 0 ]; then 
      echo "Failed to install"
      exit 1
   fi

   popd
done

exit 0

