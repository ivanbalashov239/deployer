from pathlib import Path
from subprocess import Popen, PIPE

import click


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
        if nixpath is None:
            nixpath = Path(self.path, "configuration.nix")

        imports = []
        if not nixpath.exists():
            localpath = nixpath.relative_to(self.path)
            realpath = Path(self.rootdir, localpath)
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
        for importfile in imports:
            importfile = Path(nixpath.parent, importfile).resolve()
            if importfile.exists():
                if not str(importfile).endswith(".nix"):
                    importfile = Path(importfile, "default.nix")
                deepimports.append(importfile)
                deepimports += self.nixfiles(importfile)

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
