QuantagVM
=========

Quantag Quantum Virtual Machine (QVM) backend for Qiskit.

Installation
------------

You can install the package from PyPI:

```bash
pip install quantag
```

Usage
-----

### Synchronous workflow (default)

```python
from qiskit import QuantumCircuit
from quantag.vm import QuantagVM

# Create a simple circuit
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

# Run it on QuantagVM (sync mode, results returned immediately)
backend = QuantagVM(api_key="YOUR_API_KEY",
                    backend_type="cudaq",
                    async_mode=False)

job = backend.run(qc, shots=100)
result = job.result()
print(result.get_counts())
```

### Asynchronous workflow

In async mode, jobs are submitted to the server and you can poll for status.

```python
from qiskit import QuantumCircuit
from quantag.vm import QuantagVM

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

backend = QuantagVM(api_key="YOUR_API_KEY",
                    backend_type="cudaq",
                    async_mode=True)

job = backend.run(qc, shots=100)
print("Submitted async job:", job.job_id())
print("Initial status:", job.status())

# Wait until done and fetch results
result = job.result()
print("Async result:", result.get_counts())
```

### Environment variables

Instead of hardcoding parameters, you can set environment variables.

Linux / macOS:

```bash
export QUANTAG_API_KEY="YOUR_API_KEY"
export QUANTAG_SERVER="https://quantum.quantag-it.com/api5"
export QUANTAG_BACKEND="cudaq"
export QUANTAG_ASYNC=1
```

Windows PowerShell:

```powershell
setx QUANTAG_API_KEY "YOUR_API_KEY"
setx QUANTAG_SERVER "https://quantum.quantag-it.com/api5"
setx QUANTAG_BACKEND "cudaq"
setx QUANTAG_ASYNC 1
```

Then in Python you can simply do:

```python
from qiskit import QuantumCircuit
from quantag.vm import QuantagVM

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

backend = QuantagVM()  # picks up env vars automatically
job = backend.run(qc, shots=1000)
print(job.result().get_counts())
```

License
-------

MIT License. See LICENSE file for details.
