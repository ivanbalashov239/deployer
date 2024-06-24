import pytest
import tempfile
import shutil
from pathlib import Path
from subprocess import Popen, PIPE, run


@pytest.fixture(scope="session")
def test_repo():
    with tempfile.TemporaryDirectory() as tmp:
        for file in Path(Path(__file__).parent, "test_repo").iterdir():
            shutil.copytree(file, Path(tmp, file.name))
        yield tmp


@pytest.fixture(scope="session")
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

@pytest.fixture(scope="session")
def test_vm(test_path):
    buildvm = Popen("nixos-rebuild build-vm --flake ./etc/nixos/#test", cwd=Path(test_path), shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    buildvm.wait()
    env = {"QEMU_NET_OPTS": "hostfwd=tcp::2221-:22"}
    vm = Popen("result/bin/run-nixos-vm --nographic", cwd=Path(test_path), shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, env=env)
    yield vm
    vm.kill()



@pytest.fixture(scope="session")
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

        original_files = get_files(original)
        files_in_repo = get_files(repo, base=Path(test_repo, "hosts/testhost"))
        assert original_files == files_in_repo
    return f

# @pytest.fixture(scope="session")
# def vmimage(test_path):
#     uuid="023fc77c-1c63-4f0f-827a-07fcbff4bfca"
#     with tempfile.NamedTemporaryFile() as tmp1:
#         path = tmp1.name
#         with tempfile.NamedTemporaryFile() as tmp:
#             name = tmp.name
#             run(["qemu-img", "create", "-f", "raw", name, "1G"])
#             run(["mkfs.ext4", name, "-U", uuid, "-L", "nixos"])
#             run(["qemu-img", "convert", "-f", "raw", "-O", "qcow2", name, path])
#         yield path
#
# @pytest.fixture(scope="session")
# def test_vm(vmimage, test_path):
#     buildvm = Popen(f"nixos-rebuild build --flake ./etc/nixos/#test", cwd=Path(test_path), shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
#     buildvm.wait()
#     QEMU_NET_OPTS = "hostfwd=tcp::2221-:22"
#     vm = Popen(["qemu-kvm",
#                 # "-cpu max",
#                 # "-name testhost",
#                 "-m 1024",
#                 "-smp 1",
#                 "-device virtio-rng-pci",
#                 f"-net nic,netdev=user.0,model=virtio -netdev user,id=user.0,\"{QEMU_NET_OPTS}\"",
#                 "-virtfs local,path=/nix/store,security_model=none,mount_tag=nix-store",
#                 # "-virtfs local,path="${SHARED_DIR:-$TMPDIR/xchg}",security_model=none,mount_tag=shared \
#                 # -virtfs local,path="$TMPDIR"/xchg,security_model=none,mount_tag=xchg \
#                 f"-drive cache=writeback,file=\"{vmimage}\",id=drive1,if=none,index=1,werror=report -device virtio-blk-pci,bootindex=1,drive=drive1,serial=root",
#                 "-device virtio-keyboard",
#                 "-usb",
#                 "-device usb-tablet,bus=usb-bus.0 ",
#                 "-kernel",
#                 Path(test_path, "result", "kernel").resolve(),
#                 "-initrd",
#                 Path(test_path, "result", "initrd").resolve(),
#                 "-append",
#                 Path(test_path, "result", "kernel-params").read_text().split("\n")[0].strip(),
#                 f"init={Path(test_path, 'result', 'init').resolve()}",
#                 "regInfo=/nix/store/drqsamcgqkbvkkx1v0dq86x4llxmibrf-closure-info/registration",
#                 "console=ttyS0,115200n8 console=tty0"
#                 ])
#     yield vm
#     vm.kill()
