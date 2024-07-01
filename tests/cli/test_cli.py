import time
from pathlib import Path

from click.testing import CliRunner

from deployer.main import cli
import pytest


def ids(x):
    if len(x) < 10:
        return x
    return ""


class TestCli:
    @pytest.mark.parametrize("command, outputs", [
        ["dry-build", ["""git init; git add *; git add .*
cd hosts/testhost
waiting: nixos-rebuild dry-build --flake ./#testhost
completed""", "end of dry-build"]],
        ["build", ["""git init; git add *; git add .*
cd hosts/testhost
waiting: nixos-rebuild dry-build --flake ./#testhost
completed""", "end of dry-build", """cd hosts/testhost
rsync -e 'ssh -oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -p {available_port} -i {test_path}/etc/ssh/ssh_host_ed25519_key' -rvh --chown=root:root ./ root@localhost:/etc/nixos
ssh -oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -p {available_port} -i {test_path}/etc/ssh/ssh_host_ed25519_key root@localhost nixos-rebuild build --flake /etc/nixos/#testhost"""]],
        ["test", ["""git init; git add *; git add .*
cd hosts/testhost
waiting: nixos-rebuild dry-build --flake ./#testhost
completed""", "end of dry-build", """cd hosts/testhost
rsync -e 'ssh -oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -p {available_port} -i {test_path}/etc/ssh/ssh_host_ed25519_key' -rvh --chown=root:root ./ root@localhost:/etc/nixos
ssh -oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -p {available_port} -i {test_path}/etc/ssh/ssh_host_ed25519_key root@localhost nixos-rebuild test --flake /etc/nixos/#testhost"""]],
        ["switch", ["""git init; git add *; git add .*
cd hosts/testhost
waiting: nixos-rebuild dry-build --flake ./#testhost
completed""", "end of dry-build", """cd hosts/testhost
rsync -e 'ssh -oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -p {available_port} -i {test_path}/etc/ssh/ssh_host_ed25519_key' -rvh --chown=root:root ./ root@localhost:/etc/nixos
ssh -oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -p {available_port} -i {test_path}/etc/ssh/ssh_host_ed25519_key root@localhost nixos-rebuild switch --flake /etc/nixos/#testhost"""]],
    ], ids=ids)
    def test_rebuild(self, test_repo, test_path, test_vm, test_sshkey, command, monkeypatch, available_port, outputs):
        runner = CliRunner(mix_stderr=False)
        monkeypatch.chdir(test_repo)
        sshargs = f"-oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -p {available_port} -i {test_sshkey}"
        env = {"SSH_ARGS": sshargs}
        result = runner.invoke(cli, ["rebuild", command, "testhost", "root@localhost"], env=env, )
        for i, line in enumerate(outputs):
            outputs[i] = line.format(test_path=test_path, available_port=available_port)
        assert result.exit_code == 0, result.stderr
        missing = []
        for output in outputs:
            if output not in result.stdout:
                missing.append(output)
        assert len(missing) == 0, f"missing: {missing}\n{result.stdout}\nmissing: {missing}"

    def test_newhost(self, test_repo, monkeypatch):
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
        configurationnix = Path(test_repo, "hosts/newtesthost/configuration.nix")
        assert configurationnix.exists()
        flakenix = Path(test_repo, "hosts/newtesthost/flake.nix")
        assert flakenix.exists()

    def test_init_newhost(self, test_repo, test_path, test_vm, test_sshkey, monkeypatch, available_port):
        monkeypatch.chdir(test_repo)
        runner = CliRunner(mix_stderr=False)
        monkeypatch.chdir(test_repo)
        sshargs = f"-oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -p {available_port} -i {test_sshkey}"
        env = {"SSH_ARGS": sshargs}
        result = runner.invoke(cli, ["rebuild", "init", "newtesthost", "root@localhost"],
                               input="y\nfakekey\nfakekey2\ny\n", env=env)
        assert result.exit_code == 0, result.stderr

    @pytest.mark.parametrize(["input_names"], [
        [[]],
        [["nixpkgs"]],
        [["nixpkgs", "nixos"]],
        [["nixpkgs", "agenix"]]
    ], ids=lambda x: f"inputs={x}")
    def test_update(self, test_repo, test_path, test_sshkey, monkeypatch, input_names, available_port):
        time.sleep(30)
        monkeypatch.chdir(test_repo)
        runner = CliRunner(mix_stderr=False)
        sshargs = f"-oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -p {available_port} -i {test_sshkey}"
        env = {"SSH_ARGS": sshargs}
        args = ["update", "testhost"]
        if len(input_names) > 0:
            for i in input_names:
                args.append("-i")
                args.append(i)
        result = runner.invoke(cli, args, env=env)
        assert result.exit_code == 0, result.stderr
