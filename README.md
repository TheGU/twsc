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

### 3. Install ibapi from source

**Important**: The `ibapi` package must be installed from the official Interactive Brokers TWS API package, as the PyPI version (9.87) is outdated and incompatible with current TWS clients (10.30+).

#### Option A: Use the provided scripts (recommended)

**Windows PowerShell:**
```powershell
.\scripts\install_ibapi.ps1
```

**Linux/macOS:**
```sh
./scripts/install_ibapi.sh
```

#### Option B: Manual installation

1. Download the TWS API package from https://interactivebrokers.github.io/#
   - **Windows**: Download `twsapi_windows.1030.01.msi`
   - **Linux/macOS**: Download `twsapi_macunix.1030.01.zip`

2. Install the TWS API package
3. Navigate to the pythonclient directory:
   ```sh
   cd ${TWS_API_INSTALLATION_FOLDER}/source/pythonclient/
   python setup.py install
   ```

#### Verify installation

```sh
uv pip freeze | grep ibapi
```
The output should show:
```sh
ibapi==10.37.2
```


## Usage

Import and use the `twsc` package in your Python scripts.

## Notes

- The `ibapi` package should be installed from the official TWS API package, not from PyPI. See `requirements.txt` for details.
