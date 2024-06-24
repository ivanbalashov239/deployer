{ config, lib, pkgs, ... }: {
  environment.etc."ssh/ssh_host_ed25519_key".source = ../ssh/ssh_host_ed25519_key;
  environment.etc."ssh/ssh_host_ed25519_key.pub".source = ../ssh/ssh_host_ed25519_key.pub;
  services.openssh = {
    enable = true;
    settings.PasswordAuthentication = true;
  };
  users.users.root.openssh.authorizedKeys.keys = [
      "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBiBw6GeAgYO2ZDwE7ZCHtXdI1mzP/F49ygjESd7cl22 user@testhost"
  ];


}
