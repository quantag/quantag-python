import os
import uuid
import base64
import requests
from qiskit.providers import BackendV2, JobV1, JobStatus
from qiskit.result import Result
from qiskit.transpiler import Target
from qiskit.circuit import QuantumCircuit
from qiskit.qasm2 import dumps as qasm2_dumps

class QuantagVMJob(JobV1):
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

    def __init__(self, api_key=None, server_url=None, backend_type="cudaq", request_timeout=None):
        super().__init__(
            name="QuantagVM",
            description="Quantag Quantum Simulator",
            backend_version="0.3",
        )
        self._target = Target(description="Quantag Target")

        # Auth / endpoint
        self.api_key = api_key or os.getenv("QUANTAG_API_KEY")
        base = server_url or os.getenv("QUANTAG_SERVER", "https://quantum.quantag-it.com/api5")
        self.server_url = base.rstrip("/")  # base like https://.../api5
        self.backend_type = backend_type

        # HTTP timeout (seconds)
        self.request_timeout = request_timeout or int(os.getenv("QUANTAG_TIMEOUT", "60"))

        if not self.api_key:
            raise ValueError("API key not provided. Use api_key=... or set QUANTAG_API_KEY env variable.")

    @property
    def target(self):
        return self._target

    @property
    def max_circuits(self):
        return None

    @classmethod
    def _default_options(cls):
        return {}

    def run(self, run_input, **options):
        # Accept single circuit or list
        circuits = [run_input] if isinstance(run_input, QuantumCircuit) else list(run_input)

        shots = int(options.get("shots", 1024))
        timeout = int(options.get("timeout", self.request_timeout))
        endpoint = f"{self.server_url}/qvm/run"

        results = []

        for circuit in circuits:
            # Export to OpenQASM 2.0 and base64-encode as required by Node A
            #qasm_text = circuit.qasm()
            qasm_text = qasm2_dumps(circuit)
            qasm_b64 = base64.b64encode(qasm_text.encode("utf-8")).decode("ascii")

            payload = {
                "apikey": self.api_key,
                "backend": self.backend_type,   # currently unused by Node A, but kept for future routing
                "qasm": qasm_b64,               # Node A expects key "qasm" containing base64
                "shots": shots,
            }

            # Call Node A
            resp = requests.post(endpoint, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()

            # Node A returns: { backend, shots, user_id, results: { histogram: {...}, creg_size: N } }
            hist = {}
            if "results" in data and isinstance(data["results"], dict):
                raw = data["results"].get("histogram", {}) or {}
            else:
                # Fallbacks if shape ever changes
                raw = data.get("histogram", {}) or data.get("counts", {}) or {}

            # Ensure string keys and int values
            for k, v in raw.items():
                hist[str(k)] = int(v)

            results.append({
                "success": True,
                "header": {"name": circuit.name},
                "shots": shots,
                "data": {"counts": hist},
            })

        result = Result.from_dict({
            "backend_name": self.name,
            "backend_version": self.backend_version,
            "success": True,
            "results": results,
        })

        return QuantagVMJob(self, result)
