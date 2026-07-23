{ inputs, ... }:
inputs.nixpkgs.lib.extend (
  _final: prev: {
    maintainers = prev.maintainers // {
      leoank = {
        github = "leoank";
        githubId = 22383963;
        name = "Ankur Kumar";
      };
    };
  }
)
