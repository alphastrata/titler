{
  description = "PDF Titler Project";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };


  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { 
          config.cudaSupport = true;
          inherit system;
        };
      in
      {
        devShell = pkgs.mkShell {
          buildInputs = with pkgs; [
            python311
            python311Packages.pip
            poetry
            stdenv.cc.cc.lib
          ];
          shellHook = ''
            export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH

            # Set Poetry to use the current Python version and activate shell
            poetry env use $(which python)
          '';
        };
      }
    );
}
