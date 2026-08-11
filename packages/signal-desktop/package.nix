{
  lib,
  flake,
  stdenv,
  stdenvNoCC,
  fetchurl,
  undmg,
  dpkg,
  autoPatchelfHook,
  wrapGAppsHook3,
  makeWrapper,
  alsa-lib,
  at-spi2-atk,
  at-spi2-core,
  atk,
  cairo,
  cups,
  dbus,
  expat,
  fontconfig,
  freetype,
  gdk-pixbuf,
  glib,
  gtk3,
  libdrm,
  libnotify,
  libpulseaudio,
  libxkbcommon,
  libsecret,
  mesa,
  nspr,
  nss,
  pango,
  systemd,
  xorg,
  libGL,
  pipewire,
}:

let
  versionData = builtins.fromJSON (builtins.readFile ./hashes.json);
  inherit (versionData) version hashes;
  platform = stdenv.hostPlatform.system;
in
if stdenv.hostPlatform.isDarwin then
  stdenvNoCC.mkDerivation {
    pname = "signal-desktop";
    inherit version;

    src = fetchurl {
      url = "https://updates.signal.org/desktop/signal-desktop-mac-universal-${version}.dmg";
      hash = hashes.${platform};
    };

    nativeBuildInputs = [ undmg ];
    sourceRoot = ".";

    dontPatchShebangs = true;
    dontStrip = true;
    dontPruneLibtoolFiles = true;

    installPhase = ''
      runHook preInstall
      mkdir -p "$out/Applications"
      cp -R "Signal.app" "$out/Applications/"
      mkdir -p "$out/bin"
      ln -s "$out/Applications/Signal.app/Contents/MacOS/Signal" "$out/bin/signal-desktop"
      runHook postInstall
    '';

    passthru.category = "Chat";

    meta = {
      description = "Private messenger for iOS, Android, macOS, Windows, and Linux";
      homepage = "https://signal.org/";
      changelog = "https://github.com/signalapp/Signal-Desktop/releases/tag/v${version}";
      license = lib.licenses.agpl3Only;
      sourceProvenance = [ lib.sourceTypes.binaryNativeCode ];
      maintainers = with flake.lib.maintainers; [ leoank ];
      mainProgram = "signal-desktop";
      platforms = lib.platforms.darwin;
    };
  }
else
  stdenv.mkDerivation {
    pname = "signal-desktop";
    inherit version;

    src = fetchurl {
      url = versionData.linuxUrl;
      hash = hashes.${platform};
    };

    nativeBuildInputs = [
      dpkg
      autoPatchelfHook
      wrapGAppsHook3
      makeWrapper
    ];

    buildInputs = [
      alsa-lib
      at-spi2-atk
      at-spi2-core
      atk
      cairo
      cups
      dbus
      expat
      fontconfig
      freetype
      gdk-pixbuf
      glib
      gtk3
      libdrm
      libnotify
      libpulseaudio
      libxkbcommon
      libsecret
      mesa
      nspr
      nss
      pango
      systemd
      libGL
      pipewire
      xorg.libX11
      xorg.libXcomposite
      xorg.libXdamage
      xorg.libXext
      xorg.libXfixes
      xorg.libXrandr
      xorg.libxcb
      xorg.libxshmfence
      xorg.libXtst
    ];

    runtimeDependencies = [ (lib.getLib systemd) ];

    unpackPhase = "dpkg-deb -x $src .";

    dontConfigure = true;
    dontBuild = true;
    dontWrapGApps = true;

    installPhase = ''
      runHook preInstall
      mkdir -p "$out"
      cp -R opt usr/share "$out/"
      mkdir -p "$out/bin"
      makeWrapper "$out/opt/Signal/signal-desktop" "$out/bin/signal-desktop" \
        "''${gappsWrapperArgs[@]}" \
        --prefix LD_LIBRARY_PATH : "${
          lib.makeLibraryPath [
            libGL
            pipewire
          ]
        }"
      substituteInPlace "$out/share/applications/signal-desktop.desktop" \
        --replace-fail "/opt/Signal/signal-desktop" "$out/bin/signal-desktop"
      runHook postInstall
    '';

    passthru.category = "Chat";

    meta = {
      description = "Private messenger for iOS, Android, macOS, Windows, and Linux";
      homepage = "https://signal.org/";
      changelog = "https://github.com/signalapp/Signal-Desktop/releases/tag/v${version}";
      license = lib.licenses.agpl3Only;
      sourceProvenance = [ lib.sourceTypes.binaryNativeCode ];
      maintainers = with flake.lib.maintainers; [ leoank ];
      mainProgram = "signal-desktop";
      platforms = [ "x86_64-linux" ];
    };
  }
