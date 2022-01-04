import os
import subprocess
import zipfile

import secrets

VERSION = '1.5.1'
NOTARISE_ZIP_FILENAME = f'yanom-v{VERSION}'


def main():
    create_zip_of_yanom()
    submit_for_notarisation()
    print('Check notarisation submission details above.  NOTE THE RequestUUID:')
    print('run "xcrun altool --notarization-info "<RequestUUID:>" --username "<user name>" --password "@keychain:<entry in keychain for altool>"')
    print('to check status and check the log file using hyperlink in response')
    print('run "3_deploy_package.py" once you have confirmation the package is notarised and no issues in the log')


def submit_for_notarisation():
    print('Submitting file for notarisation.  Note down the response ID')
    result = subprocess.run(f'./notarise.sh {secrets.USER_NAME} {secrets.KEY_CHAIN_ALTOOL_PASSWORD_ENTRY} {NOTARISE_ZIP_FILENAME}.zip', shell=True)
    print(f'exit code {result.returncode}')


def create_zip_of_yanom():
    print("Creating zip file of yanom for notarisation submission")

    inpath = "dist/yanom"
    outpath = f"{NOTARISE_ZIP_FILENAME}.zip"
    with zipfile.ZipFile(outpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(inpath, os.path.basename(inpath))


if __name__ == "__main__":
    main()
