#! /bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

python -m pip install poetry
cd promoter
python -m poetry install

# get 2 images
curl \
    -o '${SCRIPT_DIR}/logo/url-transparent-xs.png' \
    https://imagedelivery.net/stUTp7Ej9_5QujUPLiiNwQ/8c708fcd-3ff8-4981-9c4b-5b777484c900/public

curl \
    -o '${SCRIPT_DIR}/logo/live-transparent-xs.png' \
    https://imagedelivery.net/stUTp7Ej9_5QujUPLiiNwQ/de5a944e-cadf-4b05-1d99-6e394b01f800/public