# pytroshka

## Simple uncompression tool to counter Matroshka CTF challenge,written in python3

## Features
    - Supported archives format :
        - Zip
        - Tar
        - Bzip
        - Gzip
    - Auto-crack zip
    - Auto-uncompress above file format
    - Save your time



## How to install ?

### Linux (easiest)

    git clone https://github.com/hutchYy/pytroshka
    pip3 install -r requirements.txt
    python3 pytroshka -h

### Windows ( /!\ Couldn't make it works due to libmagic dependency complexity /!\\ )

    git clone https://github.com/hutchYy/pytroshka
    pip3 install -r requirements.txt
    // https://github.com/ahupp/python-magic here is all the informatioàn to try to install magic lib

### MacOs

    brew install libmagic or port install file
    git clone https://github.com/hutchYy/pytroshka
    pip3 install -r requirements.txt
    python3 pytroshka -h

## Future features :

- Add new archive type (Feel free to propose)
- Integrated timer and cpu consumption (You can use time on linux)
- If crash start automatically from the last extracted archive

Keywords : CTF, Uncompress, Zip, Tar, Bzip, John, zip2john, Gzip
