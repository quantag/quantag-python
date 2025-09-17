from qiskit import QuantumCircuit
from quantag.vm import QuantagVM

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

backend = QuantagVM()
job = backend.run(qc, shots=100)
result = job.result()

print(result.get_counts())

