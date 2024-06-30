from pathlib import Path

import pytest

from deployer.gitrepo import GitRepo


class TestGitRepo:
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
    ], ids=lambda x: x if len(x) < 20 else "")
    def test_add(self, test_repo, monkeypatch, capsys, output, verify_files):
        monkeypatch.chdir(test_repo)
        gitrepo = GitRepo(Path("hosts/testhost"))
        captured = capsys.readouterr()
        assert captured.err == ""
        assert set(captured.out.split("\n")) == set(output.format(test_repo=test_repo).split("\n"))
        assert {x.name for x in Path(test_repo, "hosts/testhost").iterdir()} == {
            ".git",
            "configs",
            "modules",
            "secrets",
            "configuration.nix",
            "flake.nix",
            "flake.lock",
            "hardware-configuration.nix"
        }
        verify_files(test_repo, ["configs", "modules", "secrets"],
                     ["hosts/testhost/configs", "hosts/testhost/modules", "hosts/testhost/secrets"])
