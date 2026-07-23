let
  flake = builtins.getFlake (toString ./..);
  # Derive systems from the flake itself so this never drifts from flake.nix
  # (e.g. when nixpkgs drops a platform such as x86_64-darwin).
  systems = builtins.attrNames (flake.packages or { });

  # Collect every (system, package) pair from the flake.
  collectPackages =
    system:
    let
      pkgs = flake.packages.${system} or { };
      names = builtins.attrNames pkgs;
    in
    builtins.map (name: {
      inherit name system;
      pkg = pkgs.${name};
    }) names;

  allPairs = builtins.concatMap collectPackages systems;

  extractMetadata =
    pkg:
    let
      license = pkg.meta.license or null;
      formatLicense =
        l:
        if builtins.isAttrs l && l ? spdxId then
          l.spdxId
        else if builtins.isAttrs l && l ? shortName then
          l.shortName
        else if builtins.isString l then
          l
        else
          "Check package";
      licenseStr =
        if license == null then
          "Check package"
        else if builtins.isList license then
          builtins.concatStringsSep " / " (builtins.map formatLicense license)
        else
          formatLicense license;

      sourceProvenance = pkg.meta.sourceProvenance or null;
      sourceType =
        if sourceProvenance != null then
          if builtins.isList sourceProvenance then
            if builtins.any (s: s.shortName or "" == "fromSource") sourceProvenance then
              "source"
            else if builtins.any (s: s.shortName or "" == "binaryNativeCode") sourceProvenance then
              "binary"
            else
              "unknown"
          else
            "unknown"
        else
          "unknown";

      platforms =
        let
          metaPlatforms = pkg.meta.platforms or [ ];
        in
        if builtins.isList metaPlatforms then metaPlatforms else [ ];
    in
    {
      description = pkg.meta.description or "No description available";
      version = pkg.version or "unknown";
      license = licenseStr;
      homepage = pkg.meta.homepage or null;
      sourceType = sourceType;
      hideFromDocs = pkg.passthru.hideFromDocs or false;
      hasMainProgram = builtins.hasAttr "mainProgram" pkg.meta;
      category = pkg.passthru.category or "Uncategorized";
      inherit platforms;
    };

  # Deduplicate by package name, keeping the first system that produced metadata.
  byName = builtins.foldl' (
    acc: entry:
    let
      pkg = entry.pkg;
      maybe =
        if pkg == null then
          null
        else
          let
            metadata = extractMetadata pkg;
          in
          if (metadata.hideFromDocs or false) || !(metadata.hasMainProgram or false) then null else metadata;
    in
    if maybe == null || acc ? ${entry.name} then acc else acc // { ${entry.name} = maybe; }
  ) { } allPairs;
in
byName
