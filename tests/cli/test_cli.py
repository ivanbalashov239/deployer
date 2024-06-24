import time
from pathlib import Path
from subprocess import Popen, PIPE
import re

from click.testing import CliRunner

from deployer.main import cli
import pytest
def ids(x):
    if len(x)< 10:
        return x
    return ""

class TestCli:
    @pytest.mark.parametrize("command, output_start, output_end", [
        ["dry-build", """git init; git add *; git add .*

-- hardlinking {test_repo}/hosts/testhost/configs --

cp -lr {test_repo}/configs {test_repo}/hosts/testhost/configs
git add {test_repo}/hosts/testhost/configs

-- hardlinking {test_repo}/hosts/testhost/modules --

cp -lr {test_repo}/modules {test_repo}/hosts/testhost/modules
git add {test_repo}/hosts/testhost/modules

-- hardlinking {test_repo}/hosts/testhost/secrets/hosts/testhost --

cp -lr {test_repo}/secrets/hosts/testhost {test_repo}/hosts/testhost/secrets/hosts/testhost
git add {test_repo}/hosts/testhost/secrets/hosts/testhost

-- removing hosts/testhost/.git --

rm -rf {test_repo}/hosts/testhost/.git
git init; git add *; git add .*
cd hosts/testhost
waiting: nixos-rebuild dry-build --flake ./#testhost
completed
building the system configuration...

warning: Git tree '{test_repo}/hosts/testhost' is dirty
""",
"""
end of dry-build

-- removing {test_repo}/hosts/testhost/configs --

rm -rf {test_repo}/hosts/testhost/configs

-- removing {test_repo}/hosts/testhost/modules --

rm -rf {test_repo}/hosts/testhost/modules

-- removing {test_repo}/hosts/testhost/secrets/hosts/testhost --

rm -rf {test_repo}/hosts/testhost/secrets/hosts/testhost

-- removing {test_repo}/hosts/testhost/secrets --

rm -rf {test_repo}/hosts/testhost/secrets

-- removing hosts/testhost/.git --

rm -rf {test_repo}/hosts/testhost/.git
"""],
        ["build", """git init; git add *; git add .*

-- hardlinking {test_repo}/hosts/testhost/configs --

cp -lr {test_repo}/configs {test_repo}/hosts/testhost/configs
git add {test_repo}/hosts/testhost/configs

-- hardlinking {test_repo}/hosts/testhost/modules --

cp -lr {test_repo}/modules {test_repo}/hosts/testhost/modules
git add {test_repo}/hosts/testhost/modules

-- hardlinking {test_repo}/hosts/testhost/secrets/hosts/testhost --

cp -lr {test_repo}/secrets/hosts/testhost {test_repo}/hosts/testhost/secrets/hosts/testhost
git add {test_repo}/hosts/testhost/secrets/hosts/testhost

-- hardlinking {test_repo}/hosts/testhost/secrets/hosts/testhost --

cp -lr {test_repo}/secrets/hosts/testhost {test_repo}/hosts/testhost/secrets/hosts/testhost
git add {test_repo}/hosts/testhost/secrets/hosts/testhost

-- removing hosts/testhost/.git --

rm -rf {test_repo}/hosts/testhost/.git
git init; git add *; git add .*
cd hosts/testhost
waiting: nixos-rebuild dry-build --flake ./#testhost
completed
building the system configuration...

warning: Git tree '{test_repo}/hosts/testhost' is dirty
""",
"""
end of dry-build
cd hosts/testhost
rsync -e 'ssh -oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -p 2221 -i {test_path}/etc/ssh/ssh_host_ed25519_key' -rvh --chown=root:root ./ root@localhost:/etc/nixos
ssh -oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -p 2221 -i {test_path}/etc/ssh/ssh_host_ed25519_key root@localhost nixos-rebuild build --flake /etc/nixos/#testhost

-- removing {test_repo}/hosts/testhost/configs --

rm -rf {test_repo}/hosts/testhost/configs

-- removing {test_repo}/hosts/testhost/modules --

rm -rf {test_repo}/hosts/testhost/modules

-- removing {test_repo}/hosts/testhost/secrets/hosts/testhost --

rm -rf {test_repo}/hosts/testhost/secrets/hosts/testhost

-- removing {test_repo}/hosts/testhost/secrets --

rm -rf {test_repo}/hosts/testhost/secrets

-- removing hosts/testhost/.git --

rm -rf {test_repo}/hosts/testhost/.git
"""],
        ["test", """git init; git add *; git add .*

-- hardlinking {test_repo}/hosts/testhost/configs --

cp -lr {test_repo}/configs {test_repo}/hosts/testhost/configs
git add {test_repo}/hosts/testhost/configs

-- hardlinking {test_repo}/hosts/testhost/modules --

cp -lr {test_repo}/modules {test_repo}/hosts/testhost/modules
git add {test_repo}/hosts/testhost/modules

-- hardlinking {test_repo}/hosts/testhost/secrets/hosts/testhost --

cp -lr {test_repo}/secrets/hosts/testhost {test_repo}/hosts/testhost/secrets/hosts/testhost
git add {test_repo}/hosts/testhost/secrets/hosts/testhost

-- hardlinking {test_repo}/hosts/testhost/secrets/hosts/testhost --

cp -lr {test_repo}/secrets/hosts/testhost {test_repo}/hosts/testhost/secrets/hosts/testhost
git add {test_repo}/hosts/testhost/secrets/hosts/testhost

-- hardlinking {test_repo}/hosts/testhost/secrets/hosts/testhost --

cp -lr {test_repo}/secrets/hosts/testhost {test_repo}/hosts/testhost/secrets/hosts/testhost
git add {test_repo}/hosts/testhost/secrets/hosts/testhost

-- removing hosts/testhost/.git --

rm -rf {test_repo}/hosts/testhost/.git
git init; git add *; git add .*
cd hosts/testhost
waiting: nixos-rebuild dry-build --flake ./#testhost
completed
building the system configuration...

warning: Git tree '{test_repo}/hosts/testhost' is dirty
""",
"""end of dry-build
cd hosts/testhost
rsync -e 'ssh -oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -p 2221 -i {test_path}/etc/ssh/ssh_host_ed25519_key' -rvh --chown=root:root ./ root@localhost:/etc/nixos
ssh -oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -p 2221 -i {test_path}/etc/ssh/ssh_host_ed25519_key root@localhost nixos-rebuild test --flake /etc/nixos/#testhost

-- removing {test_repo}/hosts/testhost/configs --

rm -rf {test_repo}/hosts/testhost/configs

-- removing {test_repo}/hosts/testhost/modules --

rm -rf {test_repo}/hosts/testhost/modules

-- removing {test_repo}/hosts/testhost/secrets/hosts/testhost --

rm -rf {test_repo}/hosts/testhost/secrets/hosts/testhost

-- removing {test_repo}/hosts/testhost/secrets --

rm -rf {test_repo}/hosts/testhost/secrets

-- removing hosts/testhost/.git --

rm -rf {test_repo}/hosts/testhost/.git
"""],
        ["switch", """git init; git add *; git add .*

-- hardlinking {test_repo}/hosts/testhost/configs --

cp -lr {test_repo}/configs {test_repo}/hosts/testhost/configs
git add {test_repo}/hosts/testhost/configs

-- hardlinking {test_repo}/hosts/testhost/modules --

cp -lr {test_repo}/modules {test_repo}/hosts/testhost/modules
git add {test_repo}/hosts/testhost/modules

-- hardlinking {test_repo}/hosts/testhost/secrets/hosts/testhost --

cp -lr {test_repo}/secrets/hosts/testhost {test_repo}/hosts/testhost/secrets/hosts/testhost
git add {test_repo}/hosts/testhost/secrets/hosts/testhost

-- hardlinking {test_repo}/hosts/testhost/secrets/hosts/testhost --

cp -lr {test_repo}/secrets/hosts/testhost {test_repo}/hosts/testhost/secrets/hosts/testhost
git add {test_repo}/hosts/testhost/secrets/hosts/testhost

-- hardlinking {test_repo}/hosts/testhost/secrets/hosts/testhost --

cp -lr {test_repo}/secrets/hosts/testhost {test_repo}/hosts/testhost/secrets/hosts/testhost
git add {test_repo}/hosts/testhost/secrets/hosts/testhost

-- hardlinking {test_repo}/hosts/testhost/secrets/hosts/testhost --

cp -lr {test_repo}/secrets/hosts/testhost {test_repo}/hosts/testhost/secrets/hosts/testhost
git add {test_repo}/hosts/testhost/secrets/hosts/testhost

-- removing hosts/testhost/.git --

rm -rf {test_repo}/hosts/testhost/.git
git init; git add *; git add .*
cd hosts/testhost
waiting: nixos-rebuild dry-build --flake ./#testhost
completed
building the system configuration...

warning: Git tree '{test_repo}/hosts/testhost' is dirty
""",
"""end of dry-build
cd hosts/testhost
rsync -e 'ssh -oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -p 2221 -i {test_path}/etc/ssh/ssh_host_ed25519_key' -rvh --chown=root:root ./ root@localhost:/etc/nixos
ssh -oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -p 2221 -i {test_path}/etc/ssh/ssh_host_ed25519_key root@localhost nixos-rebuild switch --flake /etc/nixos/#testhost

-- removing {test_repo}/hosts/testhost/configs --

rm -rf {test_repo}/hosts/testhost/configs

-- removing {test_repo}/hosts/testhost/modules --

rm -rf {test_repo}/hosts/testhost/modules

-- removing {test_repo}/hosts/testhost/secrets/hosts/testhost --

rm -rf {test_repo}/hosts/testhost/secrets/hosts/testhost

-- removing {test_repo}/hosts/testhost/secrets --

rm -rf {test_repo}/hosts/testhost/secrets

-- removing hosts/testhost/.git --

rm -rf {test_repo}/hosts/testhost/.git
"""],
    ], ids=ids)
    def test_rebuild(self, test_repo, test_path, test_vm, test_sshkey, command, monkeypatch, output_start, output_end):
        runner = CliRunner()
        monkeypatch.chdir(test_repo)
        sshargs = f"-oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -p 2221 -i {test_sshkey}"
        env = {"SSH_ARGS": sshargs}
        result = runner.invoke(cli, ["rebuild", command, "testhost", "root@localhost"], env=env)
        assert result.exit_code == 0, result.stderr
        output_start = output_start.format(test_repo=test_repo, test_path=test_path)
        output_end = output_end.format(test_repo=test_repo, test_path=test_path)
        assert result.output[:len(output_start)] == output_start
        assert result.output[-len(output_end):] == output_end


    def test_newhost(self, test_repo, capsys, monkeypatch):
        monkeypatch.chdir(test_repo)
        runner = CliRunner()
        result = runner.invoke(cli, ["newhost", "newtesthost"], input="fakekey\nfakekey2\n")
        assert result.exit_code == 0, result.stderr
        rsakey = Path(test_repo, ".secrets/hosts/newtesthost", "ssh_host_rsa_key")
        assert rsakey.exists()
        ed25519key = Path(test_repo, ".secrets/hosts/newtesthost", "ssh_host_ed25519_key")
        assert ed25519key.exists()
        rsabootkey = Path(test_repo, ".secrets/hosts/newtesthost/boot", "ssh_host_rsa_key")
        rsabootage = Path(test_repo, "secrets/hosts/newtesthost/boot", "ssh_host_rsa_key.age")
        assert rsabootkey.exists()
        assert rsabootage.exists()
        ed25519bootkey = Path(test_repo, ".secrets/hosts/newtesthost/boot", "ssh_host_ed25519_key")
        ed25519bootage = Path(test_repo, "secrets/hosts/newtesthost/boot", "ssh_host_ed25519_key.age")
        assert ed25519bootkey.exists()
        assert ed25519bootage.exists()
        tailscalekey = Path(test_repo, ".secrets/hosts/newtesthost", "tailscale.authkey")
        assert tailscalekey.exists()
        assert tailscalekey.read_text() == "fakekey"
        tailscaleage = Path(test_repo, "secrets/hosts/newtesthost", "tailscale.authkey.age")
        assert tailscaleage.exists()
        tailscalebootkey = Path(test_repo, ".secrets/hosts/newtesthost/boot", "tailscale.authkey")
        assert tailscalebootkey.exists()
        assert tailscalebootkey.read_text() == "fakekey2"
        tailscalebootage = Path(test_repo, "secrets/hosts/newtesthost/boot", "tailscale.authkey.age")
        assert tailscalebootage.exists()

