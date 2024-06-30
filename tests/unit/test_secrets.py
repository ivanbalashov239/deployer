from pathlib import Path

import pytest

from deployer.gitrepo import GitRepo
from deployer.secrets import SecretsNix


class TestSecrets:

    @pytest.mark.parametrize("output", [
        """git init; git add *; git add .*

-- hardlinking {test_repo}/hosts/testhost/configs --

cp -lr {test_repo}/configs {test_repo}/hosts/testhost/configs
git add {test_repo}/hosts/testhost/configs

-- hardlinking {test_repo}/hosts/testhost/modules --

cp -lr {test_repo}/modules {test_repo}/hosts/testhost/modules
git add {test_repo}/hosts/testhost/modules

-- hardlinking {test_repo}/hosts/testhost/secrets/hosts/testhost --

cp -lr {test_repo}/secrets/hosts/testhost {test_repo}/hosts/testhost/secrets/hosts/testhost
git add {test_repo}/hosts/testhost/secrets/hosts/testhost

-- removing {test_repo}/hosts/testhost/configs/default.nix --

rm -rf {test_repo}/hosts/testhost/configs/default.nix

-- removing {test_repo}/hosts/testhost/configs/boot/fixage.nix --

rm -rf {test_repo}/hosts/testhost/configs/boot/fixage.nix

-- removing {test_repo}/hosts/testhost/configs/audio/default.nix --

rm -rf {test_repo}/hosts/testhost/configs/audio/default.nix

-- removing {test_repo}/hosts/testhost/configs/users/configurator/default.nix --

rm -rf {test_repo}/hosts/testhost/configs/users/configurator/default.nix

-- removing {test_repo}/hosts/testhost/configs/system/default.nix --

rm -rf {test_repo}/hosts/testhost/configs/system/default.nix

-- removing {test_repo}/hosts/testhost/configs/system/network/default.nix --

rm -rf {test_repo}/hosts/testhost/configs/system/network/default.nix

-- removing {test_repo}/hosts/testhost/configs/system/locale/default.nix --

rm -rf {test_repo}/hosts/testhost/configs/system/locale/default.nix

-- removing {test_repo}/hosts/testhost/configs/network/ssh.nix --

rm -rf {test_repo}/hosts/testhost/configs/network/ssh.nix

-- removing {test_repo}/hosts/testhost/configs/network/tailscale.nix --

rm -rf {test_repo}/hosts/testhost/configs/network/tailscale.nix

-- removing {test_repo}/hosts/testhost/configs/boot --

rm -rf {test_repo}/hosts/testhost/configs/boot

-- removing {test_repo}/hosts/testhost/configs/audio --

rm -rf {test_repo}/hosts/testhost/configs/audio

-- removing {test_repo}/hosts/testhost/configs/users --

rm -rf {test_repo}/hosts/testhost/configs/users

-- removing {test_repo}/hosts/testhost/configs/system --

rm -rf {test_repo}/hosts/testhost/configs/system

-- removing {test_repo}/hosts/testhost/configs/network --

rm -rf {test_repo}/hosts/testhost/configs/network

-- removing hosts/testhost/.git --

rm -rf {test_repo}/hosts/testhost/.git
git init; git add *; git add .*
"""
    ], ids=lambda x: x if len(x) < 10 else "")
    def test_in_repo(self, test_repo, capsys, monkeypatch, output):
        monkeypatch.chdir(test_repo)
        secrets = SecretsNix(Path("secrets/secrets.nix"))
        gitrepo = GitRepo(Path("hosts/testhost"), secrets=secrets)
        captured = capsys.readouterr()
        assert captured.err == ""
        assert captured.out == output.format(test_repo=test_repo)
        assert secrets.files == {"hosts/testhost/secret.age": ["testhost"]}
        assert secrets.machines == {
            "testhost": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBiBw6GeAgYO2ZDwE7ZCHtXdI1mzP/F49ygjESd7cl22"}

    def test_init(self, test_repo, capsys, monkeypatch):
        monkeypatch.chdir(test_repo)
        secrets = SecretsNix(Path("secrets/secrets.nix"))
        captured = capsys.readouterr()
        assert captured.err == ""
        assert captured.out == ""
        assert secrets.files == {"hosts/testhost/secret.age": ["testhost"]}
        assert secrets.machines == {
            "testhost": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBiBw6GeAgYO2ZDwE7ZCHtXdI1mzP/F49ygjESd7cl22"}

    def test__add(self, test_repo, capsys, monkeypatch):
        newsecret = "newsecret"
        monkeypatch.chdir(test_repo)
        with open(Path(".secrets", newsecret), "w") as file:
            file.write(newsecret)
        agefile = Path(test_repo, f"secrets/{newsecret}.age")
        assert not agefile.exists()
        secrets = SecretsNix(Path(test_repo, "secrets/secrets.nix"))
        secrets.add(agefile, "testhost")
        captured = capsys.readouterr()
        assert captured.err == ""
        assert captured.out == ""
        assert secrets.files == {
            "hosts/testhost/secret.age": ["testhost"],
            f"{newsecret}.age": ["testhost"]
        }
        assert secrets.machines == {
            "testhost": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBiBw6GeAgYO2ZDwE7ZCHtXdI1mzP/F49ygjESd7cl22"}
        secrets.save()
        captured = capsys.readouterr()
        assert captured.err == ""
        # assert captured.out == "./secrets.sh  ../.secrets/\n"
        assert agefile.exists()
