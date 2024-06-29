{ config, lib, pkgs, ... }: {
    imports = [
        ./sshconfig.nix
        ./hardware-configuration.nix
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