# from deployer.deployer.something import message
import click
import socket
from pathlib import Path
from subprocess import Popen, PIPE
import re

from deployer.gitrepo import GitRepo
from deployer.secrets import SecretsNix

def mksshkey(path, keytype):
    keypath = Path(path, f"ssh_host_{keytype}_key").resolve()
    if not keypath.exists():
        sshkeygen = f"ssh-keygen -t {keytype} -f {keypath} -N ''"
        click.echo(sshkeygen)
        sh = Popen(sshkeygen, cwd=str(path), shell=True, stdin=PIPE)
        sh.wait()
    return keypath

def mktailscalekey(path, name, boot=False):
    keypath = Path(path, "tailscale.authkey").resolve()
    if boot:
        keypath = Path(path, "boot", "tailscale.authkey").resolve()
    tailscale_url = "https://login.tailscale.com/admin/settings/keys"
    click.echo(f"Please visit the following URL to create a new Tailscale auth key:\n{tailscale_url}\n")
    click.echo(f"set it to reusable")
    if boot:
        click.echo(f"tag it as boot key\nAnd make it ephemeral")
    else:
        click.echo(f"tag it with appropriate tags")
    new_key = click.prompt("Enter the new Tailscale auth key")
    with open(keypath, "w") as key_file:
        key_file.write(new_key)
    click.echo(f"Auth key for tailscale {name}, saved to {keypath}")
    return keypath


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
@click.option("--ssh-args", required=False, envvar="SSH_ARGS")
@click.pass_context
def rebuild(ctx, command, host, target, args, show_trace, ssh_args):
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
        if command == "dry-build":
            return
        click.echo(f"cd {path}")
        if target:
            if target.startswith("/"):
                rsynccmd = f"sudo rsync -rvh --chown=root:root ./ {target}"
                click.echo(rsynccmd)
                sh = Popen(rsynccmd, cwd=str(path), shell=True, stdin=PIPE)
                sh.wait()
                return
            else:
                ssh_e = ""
                if ssh_args:
                    ssh_e = f"-e 'ssh {ssh_args}'"
                rsynccmd = f"rsync {ssh_e} -rvh --chown=root:root ./ {target}:/etc/nixos"
                click.echo(rsynccmd)
                sh = Popen(rsynccmd, cwd=str(path), shell=True, stdin=PIPE)
                sh.wait()
                # nixoscmd += f" --fast --max-jobs 0 --no-build-nix --build-host '{target}' --target-host {target}"
                nixoscmd = f"ssh {ssh_args or ''} {target} nixos-rebuild {command} --flake /etc/nixos/#{path.name}"
        else:
            if command in ["test", "switch"]:
                rsynccmd = f"sudo rsync -rvh --chown=root:root ./ /etc/nixos"
                click.echo(rsynccmd)
                sh = Popen(rsynccmd, cwd=str(path), shell=True, stdin=PIPE)
                sh.wait()
                nixoscmd = f"sudo nixos-rebuild {command} --flake /etc/nixos/#{path.name}"
            else:
                nixoscmd = f"nixos-rebuild {command} --flake ./#{path.name}"
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


@cli.command()
@click.argument("name", required=True)
@click.pass_context
def newhost(ctx, name):
    path = Path(f"./hosts/{name}")
    if path.exists():
        click.echo(f"{path} already exists")
        return 1
    path.mkdir()
    click.echo(f"created {path}")
    dotsecrets = Path(".secrets", "hosts", name)
    secrets = SecretsNix(Path("secrets", "secrets.nix").resolve())
    if dotsecrets.exists():
        click.echo(f"{dotsecrets} already exists")
    else:
        Path(dotsecrets, "boot").mkdir(parents=True)
        click.echo(f"created {dotsecrets}")
        rsakey = mksshkey(Path(dotsecrets), "rsa")
        edkey = mksshkey(Path(dotsecrets), "ed25519")
        rsabootkey = mksshkey(Path(dotsecrets, "boot"), "rsa")
        edbootkey = mksshkey(Path(dotsecrets, "boot"), "ed25519")
        pubkey=Path(str(edkey)+ ".pub").read_text()
        tailkey = mktailscalekey(dotsecrets, name)
        boottailkey = mktailscalekey(dotsecrets, name, boot=True)
        for f in [rsabootkey, edbootkey, tailkey, boottailkey]:
            print("adding secret")
            print(f)
            print(dotsecrets.resolve())
            relative = f.relative_to(Path(".secrets").resolve())
            print(relative)
            path = Path(Path("secrets").resolve(), relative)
            print(path)
            secrets.add(path, name, pubkey)
        secrets.save()





if __name__ == "__main__":
    cli()
