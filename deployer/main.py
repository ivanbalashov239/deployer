# from deployer.deployer.something import message
import click
import socket
from pathlib import Path
from subprocess import Popen, PIPE, run, CompletedProcess
import re
import os
import sys
from io import BytesIO


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
            self.files[str(path)] = list(set([filekeys, host]))
        else:
            self.files[str(path)] = [host]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.save()


class GitRepo:
    created = []
    link_dirs = ["configs", "modules"]

    def __init__(self, path, secrets=None, rootdir=None):
        self.path = path.resolve()
        self.link_dirs += ["secrets/hosts/" + self.path.name]
        if not rootdir:
            rootdir = path.resolve().parent.parent
        self.rootdir = rootdir
        self.dotgit = Path(path, ".git")
        self.existing = self.dotgit.exists()
        self.secrets = secrets
        if not self.existing:
            self.gitinit()
        else:
            click.echo(f"existing git repo {path}")

        flakepath = Path(path, "flake.nix")
        # run shell command to get its output
        process = Popen(
            [f"cat {flakepath}" + " | grep \"system = \" | awk -F'\"' '{print $2}'"],
            shell=True,
            stdout=PIPE,
            stderr=PIPE,
        )
        process.wait()
        self.system = process.stdout.readline().decode().strip()
        assert self.system != ""

        self.rm_links()
        for d in self.link_dirs:
            p = Path(self.path, d)
            localpath = Path(self.path, d)
            realpath = Path(self.rootdir, d)
            localpath.parent.mkdir(parents=True, exist_ok=True)
            cmd = f"cp -lr {realpath} {localpath}"
            click.echo("")
            click.echo(f"-- hardlinking {localpath} --")
            click.echo("")
            click.echo(cmd)
            sh = Popen(
                cmd,
                cwd=str(self.path),
                shell=True,
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE,
            )
            sh.wait()
            gitinit = f"git add {localpath}"
            click.echo(gitinit)
            sh = Popen(
                gitinit,
                cwd=str(self.path),
                shell=True,
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE,
            )
            sh.wait()
        nixfiles = self.nixfiles()
        self.remove_unused(nixfiles)

    def nixfiles(self, nixpath=None):
        print("nixfiles", nixpath)
        if nixpath is None:
            nixpath = Path(self.path, "configuration.nix")

        imports = []
        if not nixpath.exists():
            localpath = nixpath.relative_to(self.path)
            realpath = Path(self.rootdir, localpath)
            print(localpath)
            print(realpath)
            nixpath = realpath
            if not nixpath.exists():
                print("not exists", nixpath)
                return imports

        with open(nixpath) as f:
            in_imports = False
            for line in f:
                line = line.strip()
                if line.startswith("imports = ["):
                    if line.endswith("];"):
                        imports += list(
                            filter(
                                lambda x: len(x) > 0,
                                line.split("[")[1].split("]")[0].split(" "),
                            )
                        )
                    else:
                        in_imports = True
                elif line.endswith("];"):
                    # Set the flag to False to indicate that we are done with the imports section
                    in_imports = False
                # Check if the flag is True and the line is not empty or a comment
                elif in_imports and line and not line.startswith("#"):
                    imports.append(line)
        deepimports = [nixpath]
        print(imports)
        for importfile in imports:
            importfile = Path(nixpath.parent, importfile).resolve()
            if importfile.exists():
                if not str(importfile).endswith(".nix"):
                    importfile = Path(importfile, "default.nix")
                deepimports.append(importfile)
                deepimports += self.nixfiles(importfile)
        print(deepimports)

        return deepimports

    def gitinit(self):
        gitinit = f"git init; git add *; git add .*"
        click.echo(gitinit)
        sh = Popen(
            gitinit,
            cwd=str(self.path),
            shell=True,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
        )
        sh.wait()

    def rm_links(self):
        for d in self.link_dirs + ["secrets"]:
            localpath = Path(self.path, d)
            realpath = Path(self.rootdir, d)
            if localpath.exists():
                assert localpath.is_dir() == True, "somehow localdir is not dir"
                self.rmrf(localpath)

    def remove_unused(self, used):
        lu = set()
        for u in used:
            lu.add(u)
            while u != self.path:
                u = u.parent
                lu.add(u)
        used = [str(x) for x in sorted(lu)]
        print("\n".join(used))
        for d in ["configs"]:
            localpath = Path(self.path, d)
            for p in localpath.rglob("*"):
                if str(p) not in used:
                    if str(p).endswith(".nix"):
                        self.rmrf(p)

        def cleandir(path):
            for p in path.glob("*"):
                if p.is_dir():
                    rfiles = list(filter(lambda x: x.is_file(), p.rglob("*")))
                    if len(rfiles) == 0:
                        self.rmrf(p)
                    else:
                        for i in p.glob("*"):
                            cleandir(i)

        for d in ["modules", "configs"]:
            localpath = Path(self.path, d)
            cleandir(localpath)

        self.rmrf(self.dotgit)
        self.gitinit()

    def add(self, path):
        localpath = Path(self.path, path)
        realpath = Path(self.rootdir, path)
        secretspath = Path(self.path, "secrets")
        if secretspath < localpath:
            if str(localpath).endswith(".age"):
                self.secrets.add(path, self.path.name)
                self.secrets.save()
            else:
                if not localpath.exists():
                    localpath.mkdir()
                tempfile = Path(localpath, ".tempfile")
                tempfile.touch()
        if realpath.exists():
            if realpath.is_dir():
                if localpath.exists() and not localpath.is_dir():
                    raise Exception(f"{path} supposed to be a directory")
                if not localpath.exists():
                    localpath.mkdir()
                tempfile = Path(localpath, ".tempfile")
                tempfile.touch()
                path = tempfile.relative_to(self.path)
            else:
                cmd = f"cp -l {realpath} {localpath}"
                sh = Popen(
                    cmd,
                    cwd=str(self.path),
                    shell=True,
                    stdin=PIPE,
                    stdout=PIPE,
                    stderr=PIPE,
                )
                sh.wait()
                self.created.append(localpath)
            gitinit = f"git add {path}"
            click.echo(gitinit)
            sh = Popen(
                gitinit,
                cwd=str(self.path),
                shell=True,
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE,
            )
            sh.wait()
        else:
            print("error")
            raise FileNotFoundError(
                f"can't link {path} to {realpath}, it doesn't exist"
            )

    def rmrf(self, path):
        cmd = f"rm -rf {path.resolve()}"
        click.echo("")
        click.echo(f"-- removing {path} --")
        click.echo("")
        click.echo(cmd)
        sh = Popen(
            cmd,
            cwd=str(self.path),
            shell=True,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
        )
        sh.wait()

    def close(self):
        self.rm_links()
        if not self.existing:
            self.rmrf(self.dotgit)
        return

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def get_hosts(host):
    if host:
        names = host.split(",")
    else:
        names = []
    paths = []
    if not names or len(names) == 0:
        paths = list(Path("./hosts").glob("*"))
    else:
        for n in names:
            path = Path(f"./hosts/{n}")
            if path.exists():
                paths.append(path)
            else:
                click.echo(f"{n} config doesn't exist")
                return None
    return paths


def dry_build(path, gitrepo, target, show_trace):
    created_files = []
    click.echo(f"cd {path}")
    clean_dry = f"nixos-rebuild dry-build --flake ./#{path.name}"

    if show_trace:
        clean_dry += f" --show-trace"
    while True:
        click.echo(f"waiting: {clean_dry}")
        sh = Popen(clean_dry, cwd=str(path), shell=True, text=True, stderr=PIPE)
        missingfiles = []
        errors = []
        while True:
            if sh.poll() is not None:
                break
            errline = sh.stderr.readline()
            if errline:
                errors.append(errline)
                missingfile = re.match(pattern, errline.strip())
                if missingfile:
                    missingfiles.append(missingfile)
        click.echo("completed")
        for missingfile in missingfiles:
            mname = missingfile.group(2)
            mpath = Path(mname)
            gitrepo.add(mpath)
        sh.wait()
        if len(missingfiles) > 0:
            click.echo("")
            click.echo("-- restarting  --")
            click.echo("")
            continue
        click.echo("\n".join(errors))

        click.echo("end of dry-build")
        return sh.returncode == 0

    nixoscmd = f"""strace -ff -e trace=file "nixos-rebuild" dry-build --flake ./#{path.name} 2>&1 | perl -ne 's/^[^"]+"(([^\\\\"]|\\\\[\\\\"nt])*)".*/$1/ && print' | grep -i {path.resolve()}"""
    sh = Popen(nixoscmd, cwd=str(path), shell=True, text=True, stdout=PIPE)
    stdout, stderr = sh.communicate()
    gitrepo.remove_unused(set(stdout.split("\n")))
    return True


def create_git(path):
    gitpath = Path(path, ".git")
    nogit = not gitpath.exists()
    if nogit:
        gitinit = f"git init; git add *; git add .*"
        click.echo(gitinit)
        sh = Popen(
            gitinit, cwd=str(path), shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE
        )
        sh.wait()
    else:
        click.echo(f"existing git repo {path}")
    return nogit


@click.group()
@click.pass_context
def cli(ctx):
    # TODO when referencing missing secrets check if they exist and if not encrypt them with host ssh key with rage-nix probably it should change configuration of secrets.nix so might be not trivial
    ctx.obj = {}
    pass


pattern = (
    r"error: getting status of '/nix/store/(.+?)/(.+?)': No such file or directory"
)


@cli.command()
@click.argument("command")
@click.argument("host", default=socket.gethostname())
@click.argument("target", required=False)
@click.argument("args", required=False, nargs=-1)
@click.option("--show-trace", is_flag=True)
@click.pass_context
def rebuild(ctx, command, host, target, args, show_trace):
    if not target and host != socket.gethostname():
        target = f"root@{host}"
    if target == "localhost":
        target = None

    paths = get_hosts(host)
    if not paths:
        return 1
    for path in paths:
        path = Path(path)
        secrets = SecretsNix(Path(path.parent.parent, "secrets/secrets.nix"))
        ctx.obj["secrets"] = ctx.with_resource(secrets)
        gitrepo = GitRepo(path, secrets=secrets)
        ctx.obj["gitrepo"] = ctx.with_resource(gitrepo)
        if not dry_build(path, gitrepo, target, show_trace):
            click.echo("dry-build failed")
            ctx.exit(1)
        click.echo(f"cd {path}")
        if target:
            if target.startswith("/"):
                rsynccmd = f"sudo rsync -rvh --chown=root:root ./ {target}"
                click.echo(rsynccmd)
                sh = Popen(rsynccmd, cwd=str(path), shell=True, stdin=PIPE)
                sh.wait()
                return
            else:
                rsynccmd = f"rsync -rvh --chown=root:root ./ {target}:/etc/nixos"
                click.echo(rsynccmd)
                sh = Popen(rsynccmd, cwd=str(path), shell=True, stdin=PIPE)
                sh.wait()
                # nixoscmd += f" --fast --max-jobs 0 --no-build-nix --build-host '{target}' --target-host {target}"
                nixoscmd = f"ssh {target} nixos-rebuild {command} --flake /etc/nixos/#{path.name}"
        else:
            rsynccmd = f"sudo rsync -rvh --chown=root:root ./ /etc/nixos"
            click.echo(rsynccmd)
            sh = Popen(rsynccmd, cwd=str(path), shell=True, stdin=PIPE)
            sh.wait()
            nixoscmd = f"sudo nixos-rebuild {command} --flake /etc/nixos/#{path.name}"
        if show_trace:
            nixoscmd += f" --show-trace"
        nixoscmd += " ".join(args)
        click.echo(nixoscmd)
        sh = Popen(nixoscmd, cwd=str(path), shell=True, stdin=PIPE)
        sh.wait()
        ctx.exit(sh.returncode)


# @cli.result_callback()
# @click.pass_context
# def on_exit(ctx, result, **kwargs):
#     print('End of start function')
#     ctx.obj["on_exit"]()


@cli.command()
@click.argument("name")
@click.argument("destination", required=False)
@click.pass_context
def deploy(ctx, name, destination):
    pass
    # if not destination:
    #    destination = name
    #    name = None
    # print(ctx, name, destination)


@cli.group()
# invoke_without_command=True)
@click.pass_context
def flake(ctx):
    if ctx.invoked_subcommand is None:
        pass
        # click.echo('I was invoked without subcommand')
    else:
        pass
        # click.echo(f"I am about to invoke {ctx.invoked_subcommand}")


@flake.command()
@click.argument("host", required=False)
@click.option("--inputname", "-i", required=False)
@click.argument("args", required=False, nargs=-1)
@click.pass_context
def update(ctx, host, inputname, args):
    paths = get_hosts(host)
    for path in paths:
        path = Path(path)
        secrets = SecretsNix(Path(path.parent.parent, "secrets/secrets.nix"))
        ctx.obj["secrets"] = ctx.with_resource(secrets)
        gitrepo = GitRepo(path, secrets=secrets)
        ctx.obj["gitrepo"] = ctx.with_resource(gitrepo)
        cmd = f"nix flake update"
        cmd += " " + " ".join(args)
        flakepath = Path(path, "flake.nix")
        if flakepath.exists():
            click.echo(f"cd {path}")
            click.echo(cmd)
            sh = Popen(cmd, cwd=str(path), shell=True, stdin=PIPE)
            sh.wait()
        else:
            click.echo(f"{flakepath} doesn't exist")
            return 1


@cli.command()
@click.argument("path", default=Path("./secrets/secrets.nix").resolve())
@click.option("--force", "-f", is_flag=True)
@click.pass_context
def secrets(ctx, path, force):
    secrets = SecretsNix(path)
    secrets.save(force)


@flake.command()
@click.argument("name", default=None)
@click.pass_context
def show(ctx, name):
    click.echo(f"flake show {name}")
    click.echo("show subcommand")


if __name__ == "__main__":
    cli()
