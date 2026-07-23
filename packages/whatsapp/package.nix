{
  lib,
  flake,
  stdenv,
  stdenvNoCC,
  fetchurl,
  undmg,
  _7zz,
}:

let
  versionData = builtins.fromJSON (builtins.readFile ./hashes.json);
  inherit (versionData) version url hashes;
  platform = stdenv.hostPlatform.system;
in
stdenvNoCC.mkDerivation {
  pname = "whatsapp";
  inherit version;

  src = fetchurl {
    inherit url;
    hash = hashes.${platform} or (throw "whatsapp: no hash for ${platform}");
  };

  nativeBuildInputs = [
    undmg
    _7zz
  ];
  sourceRoot = ".";

  dontPatchShebangs = true;
  dontStrip = true;
  dontPruneLibtoolFiles = true;

  # WhatsApp ships either an Apple-format DMG (undmg works) or, occasionally,
  # a wrapper around it that undmg refuses; fall back to 7zz which copes with
  # both APFS and HFS images and silently skips macOS xattr resource forks.
  unpackPhase = ''
    runHook preUnpack
    cp -- "$src" ./archive
    if ! undmg ./archive 2>/dev/null; then
      7zz x -snld ./archive
      find . -name '*:com.apple.*' -print -delete
    fi
    rm -f ./archive
    runHook postUnpack
  '';

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
