{
  description = "Template flake for Python projects";

  nixConfig.extra-experimental-features = "nix-command flakes recursive-nix";
  nixConfig.extra-substituters = "https://nrdxp.cachix.org https://nix-community.cachix.org";
  nixConfig.extra-trusted-public-keys = "nrdxp.cachix.org-1:Fc5PSqY2Jm1TrWfm88l6cvGWwz3s93c6IOifQWnhNW4= nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs=";
  nixConfig.extra-system-features = "recursive-nix";

  inputs = {
    nixpkgs.url = github:nixos/nixpkgs/nixos-23.11;
    flake-utils.url = github:numtide/flake-utils;
    agenix.url = "github:yaxitech/ragenix";
    agenix.inputs.nixpkgs.follows = "nixpkgs";
    poetry2nixrepo = {
      url = github:nix-community/poetry2nix;
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, agenix, poetry2nixrepo }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ agenix.overlays.default ];
        };
        dependencies = with pkgs; [ tmux git jq ragenix ];
        poetry2nix = import poetry2nixrepo { inherit pkgs; };
        deployer = poetry2nix.mkPoetryApplication {
          projectDir = ./.;
          python = pkgs.python311;
          nativeBuildInputs = dependencies;
        };
        #deployerEnv = poetry2nix.mkPoetryEnv {
        #editablePackageSources = { deployer = ./.; };
        #projectDir = ./.;
        #python = pkgs.python311;
        #nativeBuildInputs = dependencies;
        #};
        overlay = final: prev: {
          deployer = deployer;
          #deployerEnv = deployerEnv;
          #deployerTests = final.writeScriptBin "tests" ''
          #  watchexec -e py "pytest"
          #'';
        };
      in
      rec {
        devShell = pkgs.mkShell {
          buildInputs = dependencies;
          shellHook = ''${pkgs.zsh}/bin/zsh'';
        };
        apps.deployer = deployer;
        defaultApp = apps.deployer;
        defaultPackage = deployer;
        overlay = overlay;
        packages = {
          deployer = deployer;
        };
      });
}
