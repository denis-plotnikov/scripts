#!/bin/bash

#set -x

TARGET=$1
FILE_NAME="test.txt"

if [ ! -f $FILE_NAME ]; then
	echo "Here is a test text" > $FILE_NAME
fi

TEST=$(grep $TARGET $FILE_NAME)

echo ""
echo "file content:"
echo "========================="
cat test.txt
echo "========================="

if [ -z "$TEST" ];then
	echo "'$TARGET' has not been found in the file and will be added there"
	echo "$TARGET" >> $FILE_NAME
else
	echo "'$TARGET' string has been found in the file"
fi

#rm -fv test.txt
