# Edit this configuration file to define what should be installed on
# your system.  Help is available in the configuration.nix(5) man page
# and in the NixOS manual (accessible by running `nixos-help`).

{ config, pkgs, ... }: {
  imports = [
    ./hardware-configuration.nix
    # ./configs/boot/tailscale.nix
    ./configs/network/tailscale.nix
    ./configs/network/ssh.nix
    ./configs/users/configurator
    ./configs/boot/fixage.nix
    ./configs/system
    ./configs/system/locale
    ./configs/system/network
    ./configs/audio
    ./configs
  ];
  # Use the systemd-boot EFI boot loader.
  boot.loader.grub.enable = true;
  boot.loader.grub.device = "nodev";
  boot.initrd.systemd = { enable = true; };

  boot.initrd.availableKernelModules = [ "e1000" ];

  networking.hostName = "NEWHOSTNAME"; # Define your hostname.
  time.timeZone = "Asia/Jerusalem";
}
