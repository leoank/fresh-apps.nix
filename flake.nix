{
  description = "Curated, bleeding-edge Nix packages for desktop apps, updated daily.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    systems.url = "github:nix-systems/default";
    blueprint = {
      url = "github:numtide/blueprint";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.systems.follows = "systems";
    };
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    inputs:
    let
      blueprintOutputs = inputs.blueprint {
        inherit inputs;
        nixpkgs.config.allowUnfree = true;
        # nixpkgs-unstable (26.11+) dropped x86_64-darwin (Intel macOS), so we
        # only target the systems nixpkgs still supports and we ship on.
        systems = [
          "x86_64-linux"
          "aarch64-linux"
          "aarch64-darwin"
        ];
      };
    in
    blueprintOutputs
    // {
      overlays.default = import ./overlays {
        inherit (blueprintOutputs) packages;
      };
    };
}
