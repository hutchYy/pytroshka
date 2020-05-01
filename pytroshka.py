# -*- coding: utf-8 -*-

import argparse
import os
import base64
import bz2
import zipfile
import gzip
import tarfile
import magic
import subprocess

#        ___               __        ___     __                   ___  __
# |  | |  |  |__|    |    /  \ \  / |__     |__) \ /    |__| |  |  |  /  ` |__| \ / \ /
# |/\| |  |  |  |    |___ \__/  \/  |___    |__)  |     |  | \__/  |  \__, |  |  |   |


class John(object):
    def __init__(self, johnCmd, john2zipCmd):
        self.johnCmd = johnCmd
        self.john2zipCmd = john2zipCmd

    def zip2john(self, current_file: str, tmp_file: str):
        cmd = subprocess.Popen(["zip2john", current_file],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = cmd.communicate()
        if (stderr != "None"):
            with open(tmp_file, "w", encoding='utf8') as f:
                f.write(stdout.decode("utf-8"))

    def crackzip(self, tmp_file: str, wordlist: str):
        cmd = subprocess.Popen(["john", tmp_file, "--wordlist="+wordlist],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = cmd.communicate()
        return stdout, stderr

    def getPasswordFromJohn(self):
        cmd = subprocess.Popen(["john", "--show", "tmp"],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, _ = cmd.communicate()
        stdout = str(stdout.decode("utf-8"))
        if("password hashes cracked" in stdout):
            return ""
        elif("No such file or directory" in stdout):
            return ""
        else:
            return stdout.split(":")[1]


class Pytroshka(object):
    def __init__(self, pathToArchive, flagPrefix, johnCmd, john2zipCmd, wordlist):
        self.pathToArchive = pathToArchive
        self.flagPrefix = flagPrefix
        self.john = John(johnCmd, john2zipCmd)
        self.wordlist = wordlist

    def run(self):
        i = 0
        while True:
            new_file = "decompressed-" + str(i)
            # Analyzing file type.
            file_type = magic.from_file(self.pathToArchive)
            print("[*] File '{}' is '{}'.".format(self.pathToArchive, file_type))
            # Analyzing archives.
            if "bzip2" in file_type:
                self.unBzip2(new_file)

            elif "POSIX tar archive (GNU)" in file_type:
                self.unTar(new_file)

            elif "Zip" in file_type:
                self.unzip(self.pathToArchive)

            elif "ASCII text" in file_type:
                if (self.handleFlag(new_file)):
                    flag = ""
                    with open(new_file, "r") as nf:
                        flag = nf.read()
                    return flag

            elif "gzip" in file_type:
                self.unGzip(new_file)

            else:
                print("[!] Unknown archive, exiting.")
                break

            # Removing old file and going on with analysis.
            os.remove(self.pathToArchive)
            self.pathToArchive = new_file
            i += 1

    def unBzip2(self, new_file: str):
        with open(new_file, 'wb') as nf, open(self.pathToArchive, 'rb') as cf:
            decompressor = bz2.BZ2Decompressor()
            for data in iter(lambda: cf.read(100 * 1024), b''):
                nf.write(decompressor.decompress(data))

    def unTar(self, new_file):
        with tarfile.open(self.pathToArchive, 'r') as t:
            names = t.getnames()
            for name in names:
                try:
                    t.extract(name)
                    os.rename(name, new_file)
                except KeyError:
                    print('ERROR: Did not find {} in tar archive'.format(name))

    def unzip(self, new_file: str, password=""):
        with zipfile.ZipFile(self.pathToArchive) as cf:
            if len(cf.namelist()) == 1:
                file_to_be_extracted = cf.namelist()[0]
            else:
                print("[!] Too much files into the archive!")
                return
            try:
                if(password != ""):
                    cf.setpassword(password.encode("utf-8"))
                cf.extractall()
                os.rename(file_to_be_extracted, new_file)
                return True
            except RuntimeError as e:
                if ("password" in str(e)):
                    self.john.zip2john(self.pathToArchive, "tmp")
                    passwd = self.john.getPasswordFromJohn()
                    if(passwd != ""):
                        self.unzip(self.pathToArchive, passwd)
                    else:
                        self.john.crackzip("tmp", self.wordlist)
                        passwd = self.john.getPasswordFromJohn()
                        if(passwd != ""):
                            self.unzip(self.pathToArchive, passwd)

    def unGzip(self, new_file: str):
        with gzip.open(self.pathToArchive, "r") as cf:
            read_data = cf.read()
            with open(new_file, "wb") as nf:
                nf.write(read_data)

    def handleFlag(self, new_file: str):
        with open(self.pathToArchive, "r") as cf:
            encoded_data = cf.read()
            if(self.flagPrefix in encoded_data):
                print(encoded_data)
                return True
            else:
                decoded_data = base64.b64decode(encoded_data)
                if(self.flagPrefix in decoded_data):
                    print(decoded_data)
                    with open(new_file, "wb") as nf:
                        nf.write(decoded_data)
                    return True
                else:
                    return False


def parseCmd():
    parser = argparse.ArgumentParser(
        description='Simple uncompression tool for nested archives.')
    parser.add_argument('-a', action='store',
                        dest='pathToArchive', help='Path to archive')
    parser.add_argument('-p', action='store', dest='flagPrefix',
                        help='Flag prefix to stop if the flag is found')
    parser.add_argument('-w', action='store',
                        dest='pathTowordlist', help='Path to wordlist')
    parser.add_argument('-john', action='store', dest='johnCmd',
                        help='Alias of john', default="john")
    parser.add_argument('-john2zip', action='store', dest='john2zipCmd',
                        help='Alias of john2zip', default="john2zip")
    parser.add_argument('--version', action='version',
                        version='%(prog)s 1.0')
    args = parser.parse_args()
    return args.pathToArchive, args.flagPrefix, args.johnCmd, args.john2zipCmd, args.pathTowordlist


if __name__ == "__main__":
    pathToArchive, flagPrefix, johnCmd, john2zipCmd, wordlist = parseCmd()
    pytroshka = Pytroshka(pathToArchive, flagPrefix,
                          johnCmd, john2zipCmd, wordlist)
    flag = pytroshka.run()
    print(f"Here is your flag : {flag}")
