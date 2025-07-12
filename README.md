# twsc

A helper tool to trade with the Interactive Brokers TWS API.

## Requirements

- Python 3.12
- [uv](https://github.com/astral-sh/uv) (fast Python package manager)

## Setup

### 1. Create and activate a virtual environment

On Windows PowerShell:
```powershell
uv venv
.venv\Scripts\Activate.ps1
```
On Linux/macOS:
```sh
uv venv
source .venv/bin/activate
```

### 2. Install dependencies with uv

```sh
uv pip install -r requirements.txt
```

Install tws api from https://interactivebrokers.github.io/#
Then install ibapi from source package
```sh
cd ${TWS_API_INSTALLATION_FOLDER}/source/pythonclient/
python setup.py install
```

Verify ibapi version by running
```sh
uv pip freeze
```
The output should have this line
```sh
...
ibapi==10.37.2
...
```


## Usage

Import and use the `twsc` package in your Python scripts.

## Notes

- The `ibapi` package should be installed from the official TWS API package, not from PyPI. See `requirements.txt` for details.
