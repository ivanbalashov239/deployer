{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11";
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";

    home-manager.url = "github:nix-community/home-manager/release-23.11";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";

    home-manager-unstable.url = "github:nix-community/home-manager";
    home-manager-unstable.inputs.nixpkgs.follows = "nixpkgs-unstable";

    nix-darwin.url = "github:LnL7/nix-darwin";
    nix-darwin.inputs.nixpkgs.follows = "nixpkgs";

    verify-archive.url = "github:reckenrode/verify-archive/releases";
    verify-archive.inputs.nixpkgs.follows = "nixpkgs";

    agenix.url = "github:ryantm/agenix";
    # agenix.url = "github:yaxitech/ragenix";
    agenix.inputs.nixpkgs.follows = "nixpkgs";

    vscode-server.url = "github:nix-community/nixos-vscode-server";
    vscode-server.inputs.nixpkgs.follows = "nixpkgs";


    nur.url = "github:nix-community/NUR";

#    deployer.url = "path:/home/ivn/projects/deployer";
#    deployer.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    { self
    , nixpkgs
    , nixpkgs-unstable
    , nix-darwin
    , home-manager
    , home-manager-unstable
    , agenix
    , vscode-server
    , nur
#    , deployer
    , ...
    }@inputs:
    let
      modules =
        import ./modules/top-level/all-modules.nix { inherit (nixpkgs) lib; };
      system = "x86_64-linux";

    in
    {
      darwinConfigurations = { };

      nixosConfigurations = {

        NEWHOSTNAME = nixpkgs.lib.nixosSystem {
          system = system;
          modules = [
            ./configuration.nix
            nur.nixosModules.nur
#            ({ config, pkgs, ... }: {
#              nixpkgs.overlays = [
#                (final: prev:
#                  {
#                    deployer = deployer.packages.${system}.deployer;
#                  })
#              ];
#            })
            { _module.args = { inherit inputs; }; }
            ({ ... }: {
              imports = [
              ];
              disabledModules = [ ];
            })
            ({ config, pkgs, ... }: {
              nixpkgs.overlays = [
                nur.overlay
              ];
            })
            ({ config, pkgs, ... }: {
              nixpkgs.overlays = [
                (final: prev:
                  let
                    unstablePkgs = import nixpkgs-unstable { inherit (prev) system; config.allowUnfree = true; };
                  in
                  {
                    unstable = unstablePkgs;
                  })
              ];
            })
            ({ config, pkgs, ... }: {
              nixpkgs.overlays = [ agenix.overlays.default ];
            })
            ({ config, pkgs, ... }: {
              nixpkgs.overlays = [
                (self: super: {
                  fcitx-engines = pkgs.fcitx5;
                })
              ];
            })
            vscode-server.nixosModules.default
            home-manager.nixosModules.home-manager
            {
              home-manager.useGlobalPkgs = true;
              home-manager.useUserPackages = true;
              # Optionally, use home-manager.extraSpecialArgs to pass
              # arguments to home.nix
            }
            agenix.nixosModules.age
            #(final: prev: rec {
            #})
          ] ++ modules.nixos;
        };
      };

      homeModules = { };
    };
}
