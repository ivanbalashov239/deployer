{ config, lib, pkgs, ... }: {
    imports = [
    ];
  fileSystems."/" =
    {
      device = "/dev/disk/by-uuid/023fc77c-1c63-4f0f-827a-07fcbff4bfca";
      fsType = "ext4";
    };

  virtualisation.vmVariant = {
    virtualisation = {
      memorySize = 4048;
      cores = 8;
      graphics = false;
    };
  };
}
