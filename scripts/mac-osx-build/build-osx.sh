#! /bin/bash
# USAGE
# Run this script from the root of YANOM project `bash scripts/mac-osx-build/build-osx.sh`
VERSION="1.4.1"
#
echo "copy spec file to src folder"
cp scripts/mac-osx-build/yanom.spec src/yanom.spec
echo "activating venv"
source venv/bin/activate
cd src || exit
echo "remove old dist folder if exists"
rm -rf dist
pyinstaller --clean --noconfirm yanom.spec
mkdir dist/yanom/data
echo "copy config.ini to data folder"
cp config.ini dist/yanom/data/config.ini
cp ../scripts/mac-osx-build/entitlements.plist dist
mkdir dist/yanom/pandoc
echo "copy pandoc to package"
cp /usr/local/bin/pandoc dist/yanom/pandoc/pandoc
cd dist || exit
echo "code sign package"
codesign --deep --force --options=runtime --entitlements ./entitlements.plist --sign "Developer ID Application: Kevin Durston (4URXD6U67Z)" --timestamp ./yanom
echo "zipping packaged files"
zip -qr yanom-v"$VERSION"-osx-10.15.7.zip ./yanom
echo "copying zipping packaged files to project root dist folder"
cp yanom-v"$VERSION"-osx-10.15.7.zip ../../dist
echo "report code signing status"
spctl -a -t exec -vv ./yanom
codesign --verify --deep --strict --verbose=2 ./yanom
cd ../..
