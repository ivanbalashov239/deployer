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
        assert captured.out == output.format(test_repo=test_repo)
        assert {x.name for x in Path(test_repo, "hosts/testhost").iterdir()} == {
            ".git",
            "configs",
            "modules",
            "secrets",
            "configuration.nix",
            "flake.nix",
            "hardware-configuration.nix"
        }
        verify_files(test_repo, ["configs", "modules", "secrets"], ["hosts/testhost/configs", "hosts/testhost/modules", "hosts/testhost/secrets"])
