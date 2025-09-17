from qiskit.providers import BackendV2
from qiskit.result import Result
from qiskit.circuit import QuantumCircuit


class QuantagVM(BackendV2):
    """Quantag Quantum Virtual Machine (QVM) backend for Qiskit."""

    def __init__(self):
        super().__init__(name="QuantagVM",
                         description="Quantag Quantum Simulator",
                         backend_version="0.1")

    @classmethod
    def _default_options(cls):
        return {}

    def run(self, run_input, **options):
        if isinstance(run_input, QuantumCircuit):
            circuits = [run_input]
        else:
            circuits = run_input

        results = []
        for circuit in circuits:
            # Dummy result: always |0...0>
            counts = {"0" * circuit.num_qubits: 1024}
            results.append({
                "success": True,
                "header": {"name": circuit.name},
                "shots": 1024,
                "data": {"counts": counts}
            })

        return Result.from_dict({
            "backend_name": self.name,
            "backend_version": self.backend_version,
            "success": True,
            "results": results
        })
