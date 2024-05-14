{ config, lib, pkgs, ... }: {
    imports = [
        ./sshconfig.nix
    ];
  nixpkgs.config.allowUnfree = true;
  boot.loader.systemd-boot.enable = true;
  nix = {
    package = pkgs.nixUnstable;
    extraOptions = ''
     experimental-features = nix-command flakes
    '';
  };
  users.groups.admin = {};
  users.users = {
    admin = {
      isNormalUser = true;
      extraGroups = [ "wheel" ];
      password = "admin";
      group = "admin";
    };
  };
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

  networking.firewall.allowedTCPPorts = [ 22 ];
  environment.systemPackages = with pkgs; [
    htop
    jq
    vim
    git
  ];

  users.users.root.password = "password";
  system.stateVersion = "23.11";
}