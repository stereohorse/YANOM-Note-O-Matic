#! /bin/bash
# USAGE
# Run this script `bash notarise.sh` with four command line arguments
# first argument user name of developer account
# second key chain entry id for altool password
# third path to the zip file to be notarised

USER_NAME=$1
KEY_CHAIN_ALTOOL_PASSWORD_ENTRY=$2
FILENAME=$3

xcrun altool --notarize-app \
             --primary-bundle-id "com.kevin.durston.yanom" \
             --username "$USER_NAME" \
             --password "@keychain:$KEY_CHAIN_ALTOOL_PASSWORD_ENTRY" \
             --asc-provider "4URXD6U67Z" \
             --file "$FILENAME"

