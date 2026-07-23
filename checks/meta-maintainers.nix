{
  pkgs,
  flake,
  system,
  ...
}:

let
  inherit (pkgs) lib;

  packages = flake.packages.${system} or { };

  forced = lib.mapAttrsToList (
    _name: pkg: builtins.deepSeq (pkg.meta.maintainers or [ ]) true
  ) packages;
in
pkgs.runCommand "meta-maintainers-check"
  {
    inherit forced;
  }
  ''
    echo "All package meta.maintainers evaluated successfully"
    touch $out
  ''
