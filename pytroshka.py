# -*- coding: utf-8 -*-



import os
import base64
import bz2
import zipfile
import gzip
import tarfile
import magic
import subprocess

#       ___               __        ___     __                   ___  __               
#|  | |  |  |__|    |    /  \ \  / |__     |__) \ /    |__| |  |  |  /  ` |__| \ / \ / 
#|/\| |  |  |  |    |___ \__/  \/  |___    |__)  |     |  | \__/  |  \__, |  |  |   |                                                                                        


i = 0
current_file = "1819.gz"
flagprefix = "rtcp"

def getPasswordFromJohn():
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


def johnZip(tmp_file: str):
    cmd = subprocess.Popen(["john", tmp_file, "--wordlist=../xato-net-10-million-passwords-100.txt"],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = cmd.communicate()
    return stdout, stderr


def zip2john(current_file: str, tmp_file: str):
    cmd = subprocess.Popen(
        ["zip2john", current_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = cmd.communicate()
    if (stderr != "None"):
        with open(tmp_file, "w", encoding='utf8') as f:
            f.write(stdout.decode("utf-8"))


def unzip(current_file: str, password=""):
    with zipfile.ZipFile(current_file) as cf:
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
                zip2john(current_file, "tmp")
                passwd = getPasswordFromJohn()
                if(passwd != ""):
                    unzip(current_file, passwd)
                else:
                    johnZip("tmp")
                    passwd = getPasswordFromJohn()
                    if(passwd != ""):
                        unzip(current_file, passwd)


while True:
    new_file = "decompressed-" + str(i)

    # Analyzing file type.
    file_type = magic.from_file(current_file)
    print("[*] File '{}' is '{}'.".format(current_file, file_type))

    # Analyzing archives.

    if "bzip2" in file_type:
        with open(new_file, 'wb') as nf, open(current_file, 'rb') as cf:
            decompressor = bz2.BZ2Decompressor()
            for data in iter(lambda: cf.read(100 * 1024), b''):
                nf.write(decompressor.decompress(data))

    elif "POSIX tar archive (GNU)" in file_type:
        with tarfile.open(current_file, 'r') as t:
            names = t.getnames()
            for name in names:
                try:
                    f = t.extract(name)
                    os.rename(name, new_file)
                except KeyError:
                    print('ERROR: Did not find {} in tar archive'.format(name))

    elif "Zip" in file_type:
        unzip(current_file)

    elif "ASCII text" in file_type:
        with open(current_file, "r") as cf:
            encoded_data = cf.read()
        if(flagprefix in encoded_data):
            print(encoded_data)
            break
        else:
            decoded_data = base64.b64decode(encoded_data)
            if(flagprefix in decoded_data):
                print(decoded_data)
                with open(new_file, "wb") as nf:
                    nf.write(decoded_data)
                break

    elif "gzip" in file_type:
        with gzip.open(current_file, "r") as cf:
            read_data = cf.read()
        with open(new_file, "wb") as nf:
            nf.write(read_data)

    else:
        print("[!] Unknown archive, exiting.")
        break

   # Removing old file and going on with analysis.
    os.remove(current_file)
    current_file = new_file
    i += 1
