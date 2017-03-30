#! /usr/bin/env python3

import sys
import os

import argparse

class Cpmod(object):
    def __init__(self, sourceSet: str, targetSet: str, mask: int, symLink: bool=False):
        self._sourceSet = sourceSet
        self._targetSet = targetSet
        self._mask = mask
        self._symLink = symLink

    @property
    def source(self) -> str:
        return self._sourceSet

    @property
    def sourceMask(self) -> int:
        return {"u": ((0o7 & self.mask) << 6),
                "g": ((0o7 & self.mask) << 3),
                "o": (0o7 & self.mask)}.get(self.source, 0)

    @property
    def target(self) -> str:
        return self._targetSet

    @property
    def targetMask(self) -> int:
        return {"u": ((0o7 & self.mask) << 6),
                "g": ((0o7 & self.mask) << 3),
                "o": (0o7 & self.mask)}.get(self.target, 0)

    @property
    def mask(self) -> int:
        return self._mask

    @property
    def symLink(self) -> bool:
        return self._symLink

    def stat(self, path: str) -> os.stat_result:
        return os.stat(path, follow_symlinks=self.symLink)

    def chmod(self, path: str, mode: int):
        if self.exists(path):
            os.chmod(path, mode=mode)
        else:
            raise ValueError("Invalid path ({path})".format(path=path))

    def isowner(self, path: str) -> bool:
        statRes = self.stat(path)
        return statRes.st_uid == os.geteuid()

    def exists(self, path: str) -> bool:
        return (os.path.exists(path) and
                (self.symLink or not os.path.islink(path)) and
                self.isowner(path))

    def isdir(self, dirpath: str) -> bool:
        return os.path.isdir(dirpath) and self.exists(dirpath)

    def isfile(self, filepath: str) -> bool:
        return os.path.isfile(filepath) and self.exists(filepath)

    def listdir(self, dirpath: str) -> list:
        return [direntry for direntry in os.listdir(dirpath) if self.exists(os.path.join(dirpath, direntry))]

    def getTargetPermissions(self, path: str) -> int:
        if not self.exists(path):
            raise ValueError("Invalid path ({path})".format(path=path))
        statRes = self.stat(path)
        permBits = statRes.st_mode & self.targetMask
        return {"u": (permBits >> 6),
                "g": (permBits >> 3),
                "o": (permBits)}.get(self.target, 0)

    def getSourcePermissions(self, path: str) -> int:
        if not self.exists(path):
            raise ValueError("Invalid path ({path})".format(path=path))
        statRes = self.stat(path)
        permBits = statRes.st_mode & self.sourceMask
        return {"u": (permBits >> 6),
                "g": (permBits >> 3),
                "o": (permBits)}.get(self.source, 0)

    def setTargetPermissions(self, path: str, permBits: int):
        if not self.exists(path):
            raise ValueError("Invalid path ({path})".format(path=path))
        statRes = self.stat(path)
        oldMode = statRes.st_mode
        newMode = (oldMode & ~self.targetMask) | {"u": ((permBits & self.mask) << 6),
                                                  "g": ((permBits & self.mask) << 3),
                                                  "o": (permBits & self.mask)}.get(self.target, 0)
        if newMode != oldMode:
            self.chmod(path, newMode)

    def cpmod(self, path: str):
        if not self.exists(path):
            raise ValueError("Invalid path ({path})".format(path=path))
        permBits = self.getSourcePermissions(path)
        self.setTargetPermissions(path, permBits)

    def walk(self, dirpath: str):
        directories = list()
        for entry in self.listdir(dirpath):
            self.cpmod(os.path.join(dirpath, entry))

            if self.isdir(entry):
                directories.append(entry)

        for directory in directories:
            self.walk(os.path.join(dirpath, directory))

    def walkAll(self, paths: list, recursive: bool=False):
        for path in paths:
            if self.isdir(path):
                self.cpmod(path)
                if recursive:
                    self.walk(path)
            elif self.isfile(path):
                self.cpmod(path)

def parseArguments(*argv):
    parser = argparse.ArgumentParser(description="cpmod - Copy Mode")

    parser.add_argument("-s", "--src", dest="source", type=str, choices=["u", "g", "o"], help="Source permissions: u - owner, g - group, o - other", required=True)
    parser.add_argument("-t", "--tar", dest="target", type=str, choices=["u", "g", "o"], help="Target permissions: u - owner, g - group, o - other", required=True)

    parser.add_argument("-v", "--verbose", action="store_true", help="Output a diagnostic for every file processed")
    parser.add_argument("-sl", "--follow-symlinks", action="store_true")
    parser.add_argument("-m", "--mask", dest="mask", type=int, choices=range(0,8), help="Permission bit mask.  Refers to each permission sets.", default=7)
    parser.add_argument("-R", "--recursive", dest="recursive", action="store_true", help="Change files and directories recursively")

    parser.add_argument("files", metavar="FILE", nargs="+")

    return parser.parse_args(args=argv)

def main(*argv):
    options = parseArguments(*argv)
    cpmod = Cpmod(options.source, options.target, options.mask)
    cpmod.walkAll(options.files, recursive=options.recursive)

if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
