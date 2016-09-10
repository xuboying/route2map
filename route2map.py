#!/usr/bin/env python3
from __future__ import print_function
import sys
import re
import os
import subprocess
import struct
import yaml
import pygmaps


def Open(filepath):
    if sys.platform.startswith('darwin'):
        subprocess.call(('open', filepath))
    elif os.name == 'nt':
        os.startfile(filepath)
    elif os.name == 'posix':
        subprocess.call(('xdg-open', filepath))


def IPToNum(ip):
    r = struct.unpack(">I", struct.pack(
        "BBBB", * map(lambda a: int(a), ip.split("."))))
    return r[0]


def GetAddress(ip):
    global index
    # print(struct.pack("bbbb", * map( lambda a : int(a), ip.split("."))))
    SEGLENGTH = 12
    U = os.path.getsize(index)
    L = 0
    ip = IPToNum(ip)
    if IPToNum("192.168.0.0") <= ip <= IPToNum("192.168.255.255"):
        return "Local"
    with open(index, 'rb') as idx:
        while True:
            M = int((int((U / SEGLENGTH - L / SEGLENGTH) / 2) +
                     L / SEGLENGTH) * SEGLENGTH)
            idx.seek(M)
            x = idx.read(4)
            n = struct.unpack(">I", x)
            n = n[0]
            # print("%s  --->  " % n, end = "")
            # print(struct.unpack("BBBB", x))
            if ip < n:
                U = M
            else:
                L = M
            if U - L == SEGLENGTH:
                idx.seek(L + 4)
                off = struct.unpack("<I", idx.read(4))
                idx.seek(L + 8)
                ll = struct.unpack("<I", idx.read(4))
                with open("db.csv", "rb") as CSV:
                    CSV.seek(off[0])
                    r = CSV.read(ll[0])
                    r = r.decode('utf8')
                    r = re.sub(r"\n", r"", r)
                    return r


def GetCoordinate(geo, addr):
    if addr == "Local":
        return None, None
    addr1 = ""
    if addr[0] in geo.keys():
        if addr[1] in geo[addr[0]].keys():
            if addr[2] in geo[addr[0]][addr[1]].keys():
                coordinate = geo[addr[0]][addr[1]][addr[2]]
                addr1 = ",".join(addr)
            else:
                coordinate = geo[addr[0]][addr[1]][
                    list(geo[addr[0]][addr[1]].keys())[2]]
                addr1 = ",".join([addr[0], addr[1], list(
                    geo[addr[0]][addr[1]].keys())[2]])
                addr1 = "~" + addr1
        else:
            coordinate = geo[addr[0]][list(geo[addr[0]].keys())[0]][list(
                geo[addr[0]][list(geo[addr[0]].keys())[0]].keys())[0]]
            addr1 = ",".join([addr[0], list(geo[addr[0]].keys())[0], list(
                geo[addr[0]][list(geo[addr[0]].keys())[0]].keys())[0]])
            addr1 = "~~" + addr1
    return addr1, coordinate


def unique(seq):
    seen = set()
    seen_add = seen.add
    return[x for x in seq if not(x in seen or seen_add(x))]
if __name__ == '__main__':
    index = "index"
    with open("geo.yml", "r") as f:
        y = f.read()
        geo = yaml.load(y)
    # p           = Popen('traceroute %s' % " ".join(sys.argv[1 : ]), stdout = PIPE, shell = True)
    coordinates = []
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        # line = p.stdout.readline()
        if re.match(r"traceroute", line):
            print(line, end="")
            continue
        M = re.search(r"^(\s*(\d+)?\s+).*?\((\d+\.\d+\.\d+\.\d+)\)", line)
        if M:
            Addr = GetAddress(M.group(3))
            if Addr != "Local" and M.group(2):
                Addr = re.sub(r'"', '', Addr)
                addr = Addr.split(',')
                addr.pop(0)
                addr.pop(0)
                addr1, coordinate = GetCoordinate(geo, addr)
                coordinates.append(coordinate)
                print("%s%-15s%s %s %s" %
                      (M.group(1), M.group(3), Addr, addr1, coordinate))
            else:
                print("%s%-15s%s" % (M.group(1), M.group(3), Addr))
        else:
            print(line, end="")
    coordinates = unique(coordinates)
    coordinates = list(
        map(lambda x: list(map(lambda y: float(y), x.split(","))), coordinates))
    if len(coordinates) == 0:
        sys.exit(0)
    mymap = pygmaps.maps(coordinates[0][0], coordinates[0][1], 2)
    mymap.addpoint(coordinates[0][0], coordinates[0][1], "#FF0000")
    mymap.addpoint(coordinates[- 1][0], coordinates[- 1][1], "#0000FF")
    for i in range(1, len(coordinates) - 1):
        mymap.addpoint(coordinates[i][0], coordinates[i][1], "#FFFF00")
    mymap.addpath(coordinates, "#FF0000")
    fn = "./mymap.html"
    mymap.draw(fn)
    url = os.path.abspath(fn)
    url = "file://" + url
    Open(url)
    # webbrowser.open_new_tab(url)
