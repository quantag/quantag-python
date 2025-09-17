import uuid
from qiskit.providers import BackendV2, JobV1, JobStatus
from qiskit.result import Result
from qiskit.circuit import QuantumCircuit
from qiskit.transpiler import Target


class QuantagVMJob(JobV1):
    """Minimal job wrapper for QuantagVM."""

    def __init__(self, backend, result):
        job_id = str(uuid.uuid4())
        super().__init__(backend, job_id)
        self._result = result

    def result(self):
        return self._result

    def status(self):
        return JobStatus.DONE

    def submit(self):
        pass


class QuantagVM(BackendV2):
    """Quantag Quantum Virtual Machine (QVM) backend for Qiskit."""

    def __init__(self):
        super().__init__(
            name="QuantagVM",
            description="Quantag Quantum Simulator",
            backend_version="0.1",
        )
        self._target = Target(description="Dummy target for QuantagVM")

    @property
    def target(self):
        return self._target

    @property
    def max_circuits(self):
        return None  # No limit

    @classmethod
    def _default_options(cls):
        return {}

    def run(self, run_input, **options):
        if isinstance(run_input, QuantumCircuit):
            circuits = [run_input]
        else:
            circuits = run_input

        results = []
        shots = options.get("shots", 1024)
        for circuit in circuits:
            # Dummy result: always |0...0>
            counts = {"0" * circuit.num_qubits: shots}
            results.append({
                "success": True,
                "header": {"name": circuit.name},
                "shots": shots,
                "data": {"counts": counts}
            })

        result = Result.from_dict({
            "backend_name": self.name,
            "backend_version": self.backend_version,
            "success": True,
            "results": results
        })

        return QuantagVMJob(self, result)
