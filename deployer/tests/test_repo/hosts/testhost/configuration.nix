# Edit this configuration file to define what should be installed on
# your system.  Help is available in the configuration.nix(5) man page
# and in the NixOS manual (accessible by running `nixos-help`).

{ config, pkgs, ... }: {
  imports = [
        ./hardware-configuration.nix
        ./configs/ssh/sshconfig.nix
  ];
  # Use the systemd-boot EFI boot loader.
#  boot.loader.systemd-boot.enable = true;
#  boot.loader.efi.canTouchEfiVariables = true;
  boot.loader.grub.device = "nodev";
  boot.initrd.systemd = { enable = true; };
  environment.systemPackages = with pkgs; [
    git
    jq
  ];
  networking.hostName = "testhost";
  system.stateVersion = "23.11";
  users.users.root.password = "password";
}
