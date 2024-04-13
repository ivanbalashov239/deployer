{
  description = "Template flake for Python projects";

  nixConfig.extra-experimental-features = "nix-command flakes recursive-nix";
  nixConfig.extra-substituters = "https://nrdxp.cachix.org https://nix-community.cachix.org";
  nixConfig.extra-trusted-public-keys = "nrdxp.cachix.org-1:Fc5PSqY2Jm1TrWfm88l6cvGWwz3s93c6IOifQWnhNW4= nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs=";
  nixConfig.extra-system-features = "recursive-nix";

  inputs = {
    nixpkgs.url = github:nixos/nixpkgs/nixos-23.05;
    flake-utils.url = github:numtide/flake-utils;
    agenix.url = "github:yaxitech/ragenix";
    agenix.inputs.nixpkgs.follows = "nixpkgs";
    poetry2nix = {
      url = github:nix-community/poetry2nix;
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, agenix, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        overlay = final: prev: {
          deployer = final.poetry2nix.mkPoetryApplication {
            projectDir = ./.;
            python = final.python311;
          };
          deployerEnv = final.poetry2nix.mkPoetryEnv {
            editablePackageSources = { deployer = ./.; };
            projectDir = ./.;
            python = final.python311;
          };
          #deployerTests = final.writeScriptBin "tests" ''
          #  watchexec -e py "pytest"
          #'';
        };
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ overlay agenix.overlays.default ];
        };
      in
      rec {
        devShell = pkgs.mkShell {
          buildInputs = with pkgs; [ deployerEnv tmux git jq ragenix ];
          shellHook = ''
            				${pkgs.zsh}/bin/zsh
            				'';
        };
        apps.deployer = pkgs.deployer;
        defaultApp = apps.deployer;
        defaultPackage = pkgs.deployer;
        overlay = overlay;
        packages = rec {
          deployer = deployer;


        };
      });
}
