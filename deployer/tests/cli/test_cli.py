import time
from pathlib import Path
from subprocess import Popen, PIPE

from click.testing import CliRunner

from deployer.main import cli
import pytest
def ids(x):
    if len(x)< 10:
        return x
    return ""

class TestCli:
    @pytest.mark.parametrize("command, output", [
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

warning: creating lock file '{test_repo}/hosts/testhost/flake.lock'

warning: Git tree '{test_repo}/hosts/testhost' is dirty

these 21 derivations will be built:

  /nix/store/1xiy8fmg4iwxk7rbaa0a46a0armfvcd4-etc-fstab.drv

  /nix/store/sr0c058p0sx4jj0vcvqqsa89yfl5cwwc-system-path.drv

  /nix/store/29b4mgs6xi6vrm02nfzi0y3xabr3n4y6-dbus-1.drv

  /nix/store/xfgw6v87jxnc2g1xs5jzxah7vs8vkk9w-X-Restart-Triggers-dbus.drv

  /nix/store/5gbrp1ll2a1kzz6pa3fnz4bkqssax7ar-unit-dbus.service.drv

  /nix/store/4larbphg5shz2x5qdip96zc3cds1gc35-user-units.drv

  /nix/store/hlir3c9b0qhg8clfdj1rpmgznz9ck730-unit-dbus.service.drv

  /nix/store/y10avrv7fhpv4yh7k3ffs1xbs3cck2pk-system-units.drv

  /nix/store/0x80z49fmjkmpq40i2q8py8v78xc20vv-etc.drv

  /nix/store/camv4wcyprq81yw12ahfjgxbzc5as037-initrd-fstab.drv

  /nix/store/235rfdnjnqdi71y8szw5gx2qw47b2syh-initrd-system.conf.drv

  /nix/store/46b66mnjlnzdp3gkrwi33hgxgxafz5ha-users-groups.json.drv

  /nix/store/c8m9riprp16b5k4hlafvcccah8wlip6c-grub-config.xml.drv

  /nix/store/64nvp5fygivcjar3l32lz0f9i5bibg7g-install-grub.sh.drv

  /nix/store/ar9ncvfjzjnbc5jdcxrb1z7164ddq7zx-initrd-nixos.conf.drv

  /nix/store/xmqh0fbipnkdcnsir2jwy1dgzvv44q9a-unit-initrd-parse-etc.service.drv

  /nix/store/dv2yqzi4i6432jk78s2chyi6ijxz3jch-initrd-units.drv

  /nix/store/y5xjw0c6hnpryxl1bf2a2a87pwnb2wca-linux-6.8.9-modules-shrunk.drv

  /nix/store/l5xb7r7p3a83fpfrgd81p5cvb00xijb8-initrd-linux-6.8.9.drv

  /nix/store/9jvaawqk8wsh7fwv5ilf9yb3d2nhsyyj-boot.json.drv

  /nix/store/yy5swahkllqx199vb6ml3kf6ky1ac5qb-nixos-system-testhost-23.11.20240512.44072e2.drv

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
./secrets.sh  ../.secrets/
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

these 21 derivations will be built:

  /nix/store/1xiy8fmg4iwxk7rbaa0a46a0armfvcd4-etc-fstab.drv

  /nix/store/sr0c058p0sx4jj0vcvqqsa89yfl5cwwc-system-path.drv

  /nix/store/29b4mgs6xi6vrm02nfzi0y3xabr3n4y6-dbus-1.drv

  /nix/store/xfgw6v87jxnc2g1xs5jzxah7vs8vkk9w-X-Restart-Triggers-dbus.drv

  /nix/store/5gbrp1ll2a1kzz6pa3fnz4bkqssax7ar-unit-dbus.service.drv

  /nix/store/4larbphg5shz2x5qdip96zc3cds1gc35-user-units.drv

  /nix/store/hlir3c9b0qhg8clfdj1rpmgznz9ck730-unit-dbus.service.drv

  /nix/store/y10avrv7fhpv4yh7k3ffs1xbs3cck2pk-system-units.drv

  /nix/store/0x80z49fmjkmpq40i2q8py8v78xc20vv-etc.drv

  /nix/store/camv4wcyprq81yw12ahfjgxbzc5as037-initrd-fstab.drv

  /nix/store/235rfdnjnqdi71y8szw5gx2qw47b2syh-initrd-system.conf.drv

  /nix/store/46b66mnjlnzdp3gkrwi33hgxgxafz5ha-users-groups.json.drv

  /nix/store/c8m9riprp16b5k4hlafvcccah8wlip6c-grub-config.xml.drv

  /nix/store/64nvp5fygivcjar3l32lz0f9i5bibg7g-install-grub.sh.drv

  /nix/store/ar9ncvfjzjnbc5jdcxrb1z7164ddq7zx-initrd-nixos.conf.drv

  /nix/store/xmqh0fbipnkdcnsir2jwy1dgzvv44q9a-unit-initrd-parse-etc.service.drv

  /nix/store/dv2yqzi4i6432jk78s2chyi6ijxz3jch-initrd-units.drv

  /nix/store/y5xjw0c6hnpryxl1bf2a2a87pwnb2wca-linux-6.8.9-modules-shrunk.drv

  /nix/store/l5xb7r7p3a83fpfrgd81p5cvb00xijb8-initrd-linux-6.8.9.drv

  /nix/store/9jvaawqk8wsh7fwv5ilf9yb3d2nhsyyj-boot.json.drv

  /nix/store/yy5swahkllqx199vb6ml3kf6ky1ac5qb-nixos-system-testhost-23.11.20240512.44072e2.drv

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
./secrets.sh  ../.secrets/
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

these 21 derivations will be built:

  /nix/store/1xiy8fmg4iwxk7rbaa0a46a0armfvcd4-etc-fstab.drv

  /nix/store/sr0c058p0sx4jj0vcvqqsa89yfl5cwwc-system-path.drv

  /nix/store/29b4mgs6xi6vrm02nfzi0y3xabr3n4y6-dbus-1.drv

  /nix/store/xfgw6v87jxnc2g1xs5jzxah7vs8vkk9w-X-Restart-Triggers-dbus.drv

  /nix/store/5gbrp1ll2a1kzz6pa3fnz4bkqssax7ar-unit-dbus.service.drv

  /nix/store/4larbphg5shz2x5qdip96zc3cds1gc35-user-units.drv

  /nix/store/hlir3c9b0qhg8clfdj1rpmgznz9ck730-unit-dbus.service.drv

  /nix/store/y10avrv7fhpv4yh7k3ffs1xbs3cck2pk-system-units.drv

  /nix/store/0x80z49fmjkmpq40i2q8py8v78xc20vv-etc.drv

  /nix/store/camv4wcyprq81yw12ahfjgxbzc5as037-initrd-fstab.drv

  /nix/store/235rfdnjnqdi71y8szw5gx2qw47b2syh-initrd-system.conf.drv

  /nix/store/46b66mnjlnzdp3gkrwi33hgxgxafz5ha-users-groups.json.drv

  /nix/store/c8m9riprp16b5k4hlafvcccah8wlip6c-grub-config.xml.drv

  /nix/store/64nvp5fygivcjar3l32lz0f9i5bibg7g-install-grub.sh.drv

  /nix/store/ar9ncvfjzjnbc5jdcxrb1z7164ddq7zx-initrd-nixos.conf.drv

  /nix/store/xmqh0fbipnkdcnsir2jwy1dgzvv44q9a-unit-initrd-parse-etc.service.drv

  /nix/store/dv2yqzi4i6432jk78s2chyi6ijxz3jch-initrd-units.drv

  /nix/store/y5xjw0c6hnpryxl1bf2a2a87pwnb2wca-linux-6.8.9-modules-shrunk.drv

  /nix/store/l5xb7r7p3a83fpfrgd81p5cvb00xijb8-initrd-linux-6.8.9.drv

  /nix/store/9jvaawqk8wsh7fwv5ilf9yb3d2nhsyyj-boot.json.drv

  /nix/store/yy5swahkllqx199vb6ml3kf6ky1ac5qb-nixos-system-testhost-23.11.20240512.44072e2.drv

end of dry-build
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
./secrets.sh  ../.secrets/
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

these 21 derivations will be built:

  /nix/store/1xiy8fmg4iwxk7rbaa0a46a0armfvcd4-etc-fstab.drv

  /nix/store/sr0c058p0sx4jj0vcvqqsa89yfl5cwwc-system-path.drv

  /nix/store/29b4mgs6xi6vrm02nfzi0y3xabr3n4y6-dbus-1.drv

  /nix/store/xfgw6v87jxnc2g1xs5jzxah7vs8vkk9w-X-Restart-Triggers-dbus.drv

  /nix/store/5gbrp1ll2a1kzz6pa3fnz4bkqssax7ar-unit-dbus.service.drv

  /nix/store/4larbphg5shz2x5qdip96zc3cds1gc35-user-units.drv

  /nix/store/hlir3c9b0qhg8clfdj1rpmgznz9ck730-unit-dbus.service.drv

  /nix/store/y10avrv7fhpv4yh7k3ffs1xbs3cck2pk-system-units.drv

  /nix/store/0x80z49fmjkmpq40i2q8py8v78xc20vv-etc.drv

  /nix/store/camv4wcyprq81yw12ahfjgxbzc5as037-initrd-fstab.drv

  /nix/store/235rfdnjnqdi71y8szw5gx2qw47b2syh-initrd-system.conf.drv

  /nix/store/46b66mnjlnzdp3gkrwi33hgxgxafz5ha-users-groups.json.drv

  /nix/store/c8m9riprp16b5k4hlafvcccah8wlip6c-grub-config.xml.drv

  /nix/store/64nvp5fygivcjar3l32lz0f9i5bibg7g-install-grub.sh.drv

  /nix/store/ar9ncvfjzjnbc5jdcxrb1z7164ddq7zx-initrd-nixos.conf.drv

  /nix/store/xmqh0fbipnkdcnsir2jwy1dgzvv44q9a-unit-initrd-parse-etc.service.drv

  /nix/store/dv2yqzi4i6432jk78s2chyi6ijxz3jch-initrd-units.drv

  /nix/store/y5xjw0c6hnpryxl1bf2a2a87pwnb2wca-linux-6.8.9-modules-shrunk.drv

  /nix/store/l5xb7r7p3a83fpfrgd81p5cvb00xijb8-initrd-linux-6.8.9.drv

  /nix/store/9jvaawqk8wsh7fwv5ilf9yb3d2nhsyyj-boot.json.drv

  /nix/store/yy5swahkllqx199vb6ml3kf6ky1ac5qb-nixos-system-testhost-23.11.20240512.44072e2.drv

end of dry-build
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
./secrets.sh  ../.secrets/
"""],
    ], ids=ids)
    def test_rebuild(self, test_repo, test_path, test_vm, test_sshkey, command, monkeypatch, output):
        runner = CliRunner()
        monkeypatch.chdir(test_repo)
        sshargs = f"-oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -p 2221 -i {test_sshkey}"
        env = {"SSH_ARGS": sshargs}
        result = runner.invoke(cli, ["rebuild", command, "testhost", "root@localhost"], env=env)
        assert result.exit_code == 0, result.stderr
        assert result.stdout == output.format(test_repo=test_repo, test_path=test_path)
