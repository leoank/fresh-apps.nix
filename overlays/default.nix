{ packages }:
final: _prev: {
  freshApps = {
    signal-desktop = packages.${final.stdenv.hostPlatform.system}.signal-desktop or null;
    whatsapp = packages.${final.stdenv.hostPlatform.system}.whatsapp or null;
  };
}
