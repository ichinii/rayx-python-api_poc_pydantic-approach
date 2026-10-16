{
  description = "model0 - C++ model with nanobind bindings and a Python library";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    in
    {
      packages = forAllSystems (pkgs: rec {
        model0 = pkgs.python3Packages.buildPythonPackage {
          pname = "model0";
          version = "0.1.0";
          pyproject = true;
          src = ./.;

          # scikit-build-core drives cmake itself.
          dontUseCmakeConfigure = true;

          nativeBuildInputs = [ pkgs.cmake pkgs.ninja ];
          buildInputs = [ pkgs.glm ];

          build-system = with pkgs.python3Packages; [ scikit-build-core nanobind ];
          dependencies = with pkgs.python3Packages; [ numpy pydantic ];

          pythonImportsCheck = [ "model0" ];
        };
        default = model0;
      });

      # nix run .# -> runs example/main.py against the built package
      apps = forAllSystems (pkgs: {
        default = {
          type = "app";
          program = toString (pkgs.writeShellScript "model0-example" ''
            exec ${pkgs.python3.withPackages (ps: [ self.packages.${pkgs.stdenv.hostPlatform.system}.model0 ])}/bin/python ${./example/main.py}
          '');
        };
      });

      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = [
            pkgs.cmake
            pkgs.ninja
            pkgs.glm
            (pkgs.python3.withPackages (ps: with ps; [
              numpy
              pydantic
              nanobind
              scikit-build-core
              pip
            ]))
          ];

          # Editable install into a venv, so `python example/main.py` just works.
          # scikit-build-core recompiles the C++ on import when sources change.
          shellHook = ''
            if [ ! -d .venv ]; then
              python -m venv --system-site-packages .venv
              .venv/bin/pip install --no-build-isolation -e . >/dev/null
            fi
            source .venv/bin/activate
          '';
        };
      });
    };
}
