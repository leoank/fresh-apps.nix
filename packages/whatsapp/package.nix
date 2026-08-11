{
  lib,
  flake,
  stdenvNoCC,
  fetchurl,
  unzip,
}:

let
  versionData = builtins.fromJSON (builtins.readFile ./hashes.json);
  inherit (versionData) version url hashes;
  platform = stdenvNoCC.hostPlatform.system;
in
stdenvNoCC.mkDerivation {
  pname = "whatsapp";
  inherit version;

  # WhatsApp ships a universal binary from a versioned zip endpoint (the same
  # scheme nixpkgs' whatsapp-for-mac uses). Unlike the "latest" endpoint, a
  # pinned ?version= URL is byte-stable, so a fixed hash holds.
  src = fetchurl {
    inherit url;
    name = "WhatsApp.zip";
    hash = hashes.${platform} or (throw "whatsapp: no hash for ${platform}");
  };

  nativeBuildInputs = [ unzip ];
  sourceRoot = ".";

  dontConfigure = true;
  dontBuild = true;

  installPhase = ''
    runHook preInstall
    mkdir -p "$out/Applications"
    cp -R "WhatsApp.app" "$out/Applications/"
    mkdir -p "$out/bin"
    ln -s "$out/Applications/WhatsApp.app/Contents/MacOS/WhatsApp" "$out/bin/whatsapp"
    runHook postInstall
  '';

  passthru.category = "Chat";

  meta = {
    description = "WhatsApp Messenger desktop client (macOS native)";
    homepage = "https://www.whatsapp.com/";
    changelog = "https://www.whatsapp.com/download";
    license = lib.licenses.unfree;
    sourceProvenance = [ lib.sourceTypes.binaryNativeCode ];
    maintainers = with flake.lib.maintainers; [ leoank ];
    mainProgram = "whatsapp";
    platforms = lib.platforms.darwin;
  };
}
