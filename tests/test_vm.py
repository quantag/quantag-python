import os
from qiskit import QuantumCircuit
from quantag.vm import QuantagVM

# Get API key from environment
api_key = os.getenv("QUANTAG_API_KEY")
if not api_key:
    raise RuntimeError("Please set QUANTAG_API_KEY environment variable")

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

backend = QuantagVM(api_key=api_key)
job = backend.run(qc, shots=100)
result = job.result()

print(result.get_counts())
