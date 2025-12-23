{
  description = "python and numpy shell";

  inputs.nixpkgs.url = "github:Nixos/nixpkgs/nixos-unstable";

  outputs =
    { nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      python = pkgs.python3.withPackages (
        python-pkgs: with python-pkgs; [
          numpy
        ]
      );
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          python
          ty
          ruff
          # uv
        ];

        PYTHONPATH = "${python}/${python.sitePackages}";
      };
    };
}
