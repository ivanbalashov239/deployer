import re
from pathlib import Path
from subprocess import Popen

import click


class SecretsNix:
    filepattern = "let\s+(.*?)\s+in.*{(.*?)}"
    machinepattern = '([a-zA-Z]+) = "(.*?)";'
    listmachinespattern = "([a-zA-Z]+) = \[(.*?)\];"
    filespattern = '^"(.*?)"\.publicKeys = ([a-zA-Z]+);'
    listfilespattern = '^"(.*?)"\.publicKeys = \[(.*?)\];'
    machines = {}
    lists = {}
    files = {}

    def __init__(self, path):
        self.path = path
        with open(path) as file:
            self._text = file.read()
        self._match = re.search(self.filepattern, self._text.strip(), re.DOTALL)
        self._machines = self._match.group(1)
        for m in self._machines.split("\n"):
            mmatch = re.search(self.machinepattern, m, re.DOTALL)
            if mmatch:
                name = mmatch.group(1).strip()
                key = mmatch.group(2).strip()
                self.machines[name] = key
            else:
                mmatch = re.search(self.listmachinespattern, m, re.DOTALL)
                if mmatch:
                    name = mmatch.group(1).strip()
                    keys = mmatch.group(2).strip().split(" ")
                    self.lists[name] = keys
        self._files = self._match.group(2)
        for m in self._files.split("\n"):
            mmatch = re.search(self.filespattern, m.strip(), re.DOTALL)
            if mmatch:
                file = mmatch.group(1).strip()
                name = mmatch.group(2).strip()
                self.files[str(file)] = name
            else:
                mmatch = re.search(self.listfilespattern, m.strip(), re.DOTALL)
                if mmatch:
                    file = mmatch.group(1).strip()
                    namelist = mmatch.group(2).strip().split(" ")
                    self.files[str(file)] = namelist

    def __str__(self):
        machines = []
        for key in self.machines.keys():
            machines.append(f'{key} = "{self.machines[key]}";')
        machines = "\n".join(machines)
        lists = []
        for key in self.lists.keys():
            newstr = " ".join(self.lists[key])
            lists.append(f"{key} = [ {newstr} ];")
        lists = "\n".join(lists)
        files = []
        for key in sorted(set(self.files.keys())):
            if type(self.files[key]) == list:
                newstr = " ".join(self.files[key])
                files.append(f'"{key}".publicKeys = [ {newstr} ];')
            else:
                files.append(f'"{key}".publicKeys = {self.files[key]};')
        files = "\n".join(files)
        return "let\n" + f"{machines}\n{lists}\nin" + "\n{\n" f"{files}" + "\n}"

    def save(self, force=False):
        with open(self.path, "w") as f:
            f.write(str(self))
        forceflag = ""
        if force:
            forceflag = "-f"
        # rootpath = self.path.parent.parent
        # originalpath = Path(rootpath, ".secrets")
        # secretspath = Path(rootpath, "secrets")
        # for name, hosts in self.files.items():
        #     if type(hosts) == list:
        #         for host in hosts:
        #             if host not in self.machines:
        #                 raise Exception(f"{host} has no key")
                    # cmd = f"cp -l {secret} {Path(secretspath, name)}"
                    # sh = Popen(cmd, cwd=rootpath, shell=True)
                    # sh.wait()
        resecret = f"./secrets.sh {forceflag} ../.secrets/"
        click.echo(resecret)
        sh = Popen(resecret, cwd=str(Path(self.path).parent), shell=True)
        sh.wait()

    def add(self, path, host, hostkey=None):
        path = path.relative_to(self.path.parent)
        if not self.machines.get(host) and not hostkey:
            raise Exception(
                f" {host} has no key, for new hosts hostkey has to be specified"
            )
        self.machines[host] = self.machines.get(host, hostkey)
        filekeys = self.files.get(str(path))
        if type(filekeys) == list:
            filekeys.append(host)
            self.files[str(path)] = list(set(filekeys))
        elif filekeys:
            self.files[str(path)] = list({filekeys, host})
        else:
            self.files[str(path)] = [host]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.save()
