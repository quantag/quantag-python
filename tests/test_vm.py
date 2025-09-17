from qiskit import QuantumCircuit, execute
from quantag.vm import QuantagVM

def test_quantagvm_runs():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()

    backend = QuantagVM()
    result = execute(qc, backend, shots=100).result()
    counts = result.get_counts()
    assert "00" in counts

