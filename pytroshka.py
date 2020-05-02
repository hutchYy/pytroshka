# -*- coding: utf-8 -*-

import argparse
import os
import base64
import bz2
import zipfile
import gzip
import tarfile
import subprocess
import shutil
import sys
if os.name == "nt":
    from winmagic import magic
else :
    import magic


#        ___               __        ___     __                   ___  __
# |  | |  |  |__|    |    /  \ \  / |__     |__) \ /    |__| |  |  |  /  ` |__| \ / \ /
# |/\| |  |  |  |    |___ \__/  \/  |___    |__)  |     |  | \__/  |  \__, |  |  |   |


class John(object):
    def __init__(self, johnCmd, zip2johnCmd):
        self.johnCmd = johnCmd
        self.zip2johnCmd = zip2johnCmd
        print(shutil.which(self.johnCmd))
        if shutil.which(self.johnCmd) == "":
            sys.exit("A password is required for the archive\njohn doesn't exist in your path or is not installed")
        if shutil.which(self.zip2johnCmd) == "":
            sys.exit("A password is required for the archive\nzip2john doesn't exist in your path or is not installed")


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
    def __init__(self, pathToArchive, flagPrefix, johnCmd, zip2johnCmd, wordlist):
        self.pathToArchive = pathToArchive
        self.flagPrefix = flagPrefix
        self.john = John(johnCmd, zip2johnCmd)
        self.wordlist = wordlist

    def run(self):
        i = 0
        while True:
            new_file = "decompressed-" + str(i)

            # Check if it exist
            if not os.path.isfile(self.pathToArchive):
                print("Error while processing the archive")
                return ""

            # Analyzing file type.
            file_type = magic.from_file(self.pathToArchive)
            print("[*] File '{}' is '{}'.".format(self.pathToArchive, file_type))

            # Analyzing archives.
            if "bzip2" in file_type:
                if self.unBzip2(new_file) :
                    print(" └ [+] bzip2 uncompresssed")
                else :
                    print(" └ [!] Error happened while trying to uncompress bzip2")

            elif "POSIX tar archive (GNU)" in file_type:
                if self.unTar(new_file) :
                    print(" └ [+] tar uncompresssed")
                else :
                    print(" └ [!] Error happened while trying to uncompress tar")

            elif "Zip" in file_type:
                if self.unzip(self.pathToArchive) :
                    print(" └ [+] zip uncompresssed")
                else :
                    print(" └ [!] Error happened while trying to crack the zip")
            elif "ASCII text" in file_type:
                if (self.handleFlag(new_file)):
                    flag = ""
                    with open(new_file, "r") as nf:
                        flag = nf.read()
                    return flag

            elif "gzip" in file_type:
                if self.unGzip(new_file) :
                    print(" └ [+] gzip uncompresssed")
                else :
                    print(" └ [!] Error happened while trying to uncompress gzip")

            else:
                print("[!] Unknown archive, exiting.")
                break

            # Removing old file and going on with analysis.
            if i > 0 :
                pass
                #os.remove(self.pathToArchive)
            self.pathToArchive = new_file
            i += 1

    def unBzip2(self, new_file: str):
        try:
            with open(new_file, 'wb') as nf, open(self.pathToArchive, 'rb') as cf:
                decompressor = bz2.BZ2Decompressor()
                for data in iter(lambda: cf.read(100 * 1024), b''):
                    nf.write(decompressor.decompress(data))
            return True
        except :
            return False       

    def unTar(self, new_file):
        with tarfile.open(self.pathToArchive, 'r') as t:
            names = t.getnames()
            for name in names:
                try:
                    t.extract(name)
                    os.rename(name, new_file)
                    return True
                except KeyError:
                    print('ERROR: Did not find {} in tar archive'.format(name))
                    return False

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
                        if(passwd != "" and passwd != "password hashes cracked, 0 left"):
                            self.unzip(self.pathToArchive, passwd)
                        else :
                            return False

    def unGzip(self, new_file: str):
        try :
            with gzip.open(self.pathToArchive, "r") as cf:
                read_data = cf.read()
                with open(new_file, "wb") as nf:
                    nf.write(read_data)
            return True
        except :
            return False

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
                        dest='pathToArchive', help='Path to archive',required=True)
    parser.add_argument('-p', action='store', dest='flagPrefix',
                        help='Flag prefix to stop if the flag is found')
    parser.add_argument('-w', action='store',
                        dest='pathTowordlist', help='Path to wordlist')
    parser.add_argument('-john', action='store', dest='johnCmd',
                        help='Alias of john', default="john")
    parser.add_argument('-zip2john', action='store', dest='zip2johnCmd',
                        help='Alias of zip2john', default="zip2john")
    parser.add_argument('--version', action='version',
                        version='%(prog)s 1.0')
    args = parser.parse_args()
    return args.pathToArchive, args.flagPrefix, args.johnCmd, args.zip2johnCmd, args.pathTowordlist


if __name__ == "__main__":
    pathToArchive, flagPrefix, johnCmd, zip2johnCmd, wordlist = parseCmd()
    pytroshka = Pytroshka(pathToArchive, flagPrefix,
                          johnCmd, zip2johnCmd, wordlist)
    flag = pytroshka.run()
    if flag != "":
        print(f"Here is your flag : {flag}")
