# rayx - c++ model with nanobind bindings and a Python library

The C++ model lives in `cpp/model0.h` and is exposed to python as the internal
`rayx._model0` module. `rayx._model1` is the user facing model, `rayx.lower`
translates between the two.

## install

using nix
```bash
nix develop
python example/main.py
```
or, without entering a shell
```bash
nix run .#
```
or
```bash
python -m venv .venv && source .venv/bin/activate
pip install .
python example/main.py
```

Note: the dev shell keeps an editable install in `.venv`. It is only created
when missing, so after renaming a module or changing dependencies, remove it
(`rm -rf .venv`) and re-enter `nix develop`.
