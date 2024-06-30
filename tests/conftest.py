import time

import pytest
import tempfile
import shutil
from pathlib import Path
from subprocess import Popen, PIPE, run


@pytest.fixture(scope="function")
def test_repo():
    with tempfile.TemporaryDirectory() as tmp:
        for file in Path(Path(__file__).parent, "test_repo").iterdir():
            shutil.copytree(file, Path(tmp, file.name))
        yield tmp


@pytest.fixture(scope="function")
def test_path():
    with (tempfile.TemporaryDirectory() as tmp):
        for file in Path(Path(__file__).parent, "test_host").iterdir():
            shutil.copytree(file, Path(tmp, file.name))
        # run git init and git add . in the test_path
        sh = Popen("git init", cwd=tmp, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        sh.wait()
        sh = Popen("git add .", cwd=tmp, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        sh.wait()
        yield tmp


@pytest.fixture(scope="function")
def available_port():
    """ get non used port"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("localhost", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture(scope="function")
def test_vm(test_path, test_sshkey, available_port):
    buildvm = Popen("nixos-rebuild build-vm --flake ./etc/nixos/#test", cwd=Path(test_path), shell=True, stdin=PIPE,
                    stdout=PIPE, stderr=PIPE)
    buildvm.wait()
    ssh_args = f"-oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -p {available_port} -i {test_sshkey}"
    ssh_args_e = f"-e 'ssh {ssh_args}'"
    env = {"QEMU_NET_OPTS": f"hostfwd=tcp::{available_port}-:22"}
    vm = Popen("result/bin/run-nixos-vm --nographic", cwd=Path(test_path), shell=True, stdin=PIPE, stdout=PIPE,
               stderr=PIPE, env=env)
    time.sleep(5)
    if vm.returncode is not None:
        raise Exception(f"vm failed to start {vm.stderr.read()}")
    rsynccmd = Popen(f"rsync {ssh_args_e} -rvha ./etc/nixos/ root@localhost:/etc/nixos/", cwd=Path(test_path),
                     shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    rsynccmd.wait()
    if rsynccmd.returncode != 0:
        raise Exception(f"rsync failed {rsynccmd.stderr.read()} {vm.stderr.read()} {vm.stdout.read()} {vm.returncode}")
    yield vm
    vm.kill()


@pytest.fixture(scope="function")
def test_sshkey(test_path):
    return Path(test_path, "etc", "ssh", "ssh_host_ed25519_key")


@pytest.fixture()
def verify_files():
    def f(test_repo, original, repo):
        def get_files(directories, base=test_repo):
            result = {}
            for directory in directories:
                for file in Path(test_repo, directory).glob('**/*'):
                    if file.is_file():
                        if file.name.startswith("secrets") and not file.name.endswith(".age"):
                            continue
                        name = str(file.relative_to(base))
                        result[name] = file.read_text()
            return result

        original_files = {i: f for i, f in get_files(original).items() if f.strip() != "{ }"}
        files_in_repo = get_files(repo, base=Path(test_repo, "hosts/testhost"))
        assert original_files == files_in_repo

    return f
