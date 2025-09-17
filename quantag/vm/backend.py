import os
import uuid
import time
import base64
import requests
from qiskit.providers import BackendV2, JobV1, JobStatus
from qiskit.result import Result
from qiskit.transpiler import Target
from qiskit.circuit import QuantumCircuit
from qiskit.qasm2 import dumps as qasm2_dumps


def _truthy(x: str) -> bool:
    return str(x).strip().lower() in ("1", "true", "yes", "on")

class QuantagVMJob(JobV1):
    """
    Job wrapper for QuantagVM.
    """

    def __init__(self, backend, job_id=None, qiskit_result: Result | None = None,
                 async_jobs: list[dict] | None = None,
                 poll_interval: float = 1.0, job_timeout: int = 600):
        super().__init__(backend=backend, job_id=job_id or str(uuid.uuid4()))
        self.backend = backend   # <-- store the QuantagVM instance here
        self._result = qiskit_result
        self._async_jobs = async_jobs or []
        self._poll_interval = float(poll_interval)
        self._job_timeout = int(job_timeout)
        self._terminal_status = None

    # ---- helpers for async path ----
    def _fetch_job_status(self, job_uid: str) -> dict:
        url = f"{self.backend.server_url}/qvm/job/{job_uid}"
        headers = {"X-API-Key": self.backend.api_key}
        resp = requests.get(url, headers=headers, timeout=self.backend.request_timeout)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _build_qiskit_result(per_circuit_counts: list[dict],
                             per_circuit_names: list[str],
                             per_circuit_shots: list[int],
                             backend_name: str,
                             backend_version: str) -> Result:
        results = []
        for counts, name, shots in zip(per_circuit_counts, per_circuit_names, per_circuit_shots):
            hist = {str(k): int(v) for k, v in (counts or {}).items()}
            results.append({
                "success": True,
                "header": {"name": name},
                "shots": shots,
                "data": {"counts": hist},
            })
        return Result.from_dict({
            "backend_name": backend_name,
            "backend_version": backend_version,
            "success": True,
            "results": results,
        })

    # ---- JobV1 API ----
    def result(self) -> Result:
        # Sync path: already have a Result
        if self._result is not None:
            return self._result

        # Async path: poll all jobs and assemble a single Result
        start = time.time()
        per_counts = []
        per_names = []
        per_shots = []

        for item in self._async_jobs:
            job_uid = item["job_uid"]
            name = item["name"]
            shots = item["shots"]

            while True:
                info = self._fetch_job_status(job_uid)
                status = (info.get("status") or "").upper()

                if status == "DONE":
                    res = info.get("results") or {}
                    counts = (res.get("histogram") if isinstance(res, dict) else {}) or {}
                    per_counts.append(counts)
                    per_names.append(name)
                    per_shots.append(shots)
                    break

                if status == "ERROR":
                    # try to surface node message if present
                    msg = res = info.get("results")
                    raise RuntimeError(f"Quantag job {job_uid} failed: {msg}")

                if (time.time() - start) > self._job_timeout:
                    raise TimeoutError(f"Timed out waiting for job {job_uid}")

                time.sleep(self._poll_interval)

        # Build and cache Result
        #self._result = self._build_qiskit_result(per_counts, per_names, per_shots)
        self._result = self._build_qiskit_result(
            per_circuit_counts=per_counts,
            per_circuit_names=per_names,
            per_circuit_shots=per_shots,
            backend_name=self.backend.name,
            backend_version=self.backend.backend_version,
        )

        self._terminal_status = JobStatus.DONE
        return self._result

    def status(self):
        # Sync job is immediately DONE
        if self._async_jobs == []:
            return JobStatus.DONE
        if self._terminal_status is not None:
            return self._terminal_status

        any_running = False
        for item in self._async_jobs:
            job_uid = item["job_uid"]
            try:
                info = self._fetch_job_status(job_uid)
                status = (info.get("status") or "").upper()
                if status == "ERROR":
                    self._terminal_status = JobStatus.ERROR
                    return self._terminal_status
                if status not in ("DONE", "ERROR"):
                    any_running = True
            except Exception:
                any_running = True  # network hiccup => treat as running

        if any_running:
            return JobStatus.RUNNING
        self._terminal_status = JobStatus.DONE
        return self._terminal_status

    def submit(self):
        # Nothing to do: submission happened in Backend.run()
        pass


class QuantagVM(BackendV2):
    """Quantag Quantum Virtual Machine (QVM) backend for Qiskit."""

    def __init__(self, api_key=None, server_url=None, backend_type="cudaq",
                 request_timeout=None, async_mode: bool | None = None,
                 poll_interval: float | None = None, job_timeout: int | None = None):
        super().__init__(
            name="QuantagVM",
            description="Quantag Quantum Simulator",
            backend_version="0.4",
        )
        self._target = Target(description="Quantag Target")

        # Auth / endpoint
        self.api_key = api_key or os.getenv("QUANTAG_API_KEY")
        base = server_url or os.getenv("QUANTAG_SERVER", "https://quantum.quantag-it.com/api5")
        self.server_url = base.rstrip("/")  # base like https://.../api5
        self.backend_type = backend_type

        # Timeouts / polling
        self.request_timeout = int(request_timeout or os.getenv("QUANTAG_TIMEOUT", "60"))
        self.poll_interval = float(poll_interval or os.getenv("QUANTAG_POLL", "1.0"))
        self.job_timeout = int(job_timeout or os.getenv("QUANTAG_JOB_TIMEOUT", "600"))

        # Async toggle (default from env, else False)
        if async_mode is None:
            self.async_mode = _truthy(os.getenv("QUANTAG_ASYNC", "0"))
        else:
            self.async_mode = bool(async_mode)

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

    def _post_sync(self, qasm_b64: str, shots: int):
        url = f"{self.server_url}/qvm/run"
        payload = {"apikey": self.api_key, "qasm": qasm_b64, "shots": shots}

        resp = requests.post(url, json=payload, timeout=60)

    # Try to parse JSON even if status != 200
        try:
           data = resp.json()
        except Exception:
            data = {"error": resp.text.strip()}

        if resp.status_code != 200:
           # Look deeper into the response for details
            err_msg = None
            if isinstance(data, dict):
                if "details" in data and isinstance(data["details"], dict):
                    err_msg = data["details"].get("error")
                if not err_msg:
                    err_msg = data.get("error")
            if not err_msg:
                err_msg = f"HTTP {resp.status_code}"
            raise RuntimeError(f"QuantagVM error: {err_msg}")

        return data


    def _submit_async(self, qasm_b64: str, shots: int) -> str:
        endpoint = f"{self.server_url}/qvm/submit"
        payload = {
            "apikey": self.api_key,
            "backend": self.backend_type,
            "qasm": qasm_b64,
            "shots": shots,
        }
        resp = requests.post(endpoint, json=payload, timeout=self.request_timeout)
        resp.raise_for_status()
        data = resp.json()
        if "job_uid" not in data:
            raise RuntimeError(f"Quantag async submit failed: {data}")
        return data["job_uid"]

    def run(self, run_input, **options):
        # Accept single circuit or list
        circuits = [run_input] if isinstance(run_input, QuantumCircuit) else list(run_input)

        shots = int(options.get("shots", 1024))

        # ---- SYNC MODE (default, current behavior) ----
        if not self.async_mode:
            per_counts = []
            per_names = []
            per_shots = []

            for circuit in circuits:
                qasm_text = qasm2_dumps(circuit)  # OpenQASM 2.0
                qasm_b64 = base64.b64encode(qasm_text.encode("utf-8")).decode("ascii")

                data = self._post_sync(qasm_b64, shots)

                # Node A returns: { backend, shots, user_id, results: { histogram: {...}, creg_size: N } }
                raw = {}
                if isinstance(data, dict):
                    if isinstance(data.get("results"), dict):
                        raw = data["results"].get("histogram", {}) or {}
                    else:
                        raw = data.get("histogram", {}) or data.get("counts", {}) or {}

                per_counts.append(raw)
                per_names.append(circuit.name)
                per_shots.append(shots)

            qiskit_result = QuantagVMJob._build_qiskit_result(
                per_circuit_counts=per_counts,
                per_circuit_names=per_names,
                per_circuit_shots=per_shots,
                backend_name=self.name,
                backend_version=self.backend_version,
            )

            # Wrap in job
            return QuantagVMJob(self, qiskit_result=qiskit_result)

        # ---- ASYNC MODE (new) ----
        async_jobs = []
        for circuit in circuits:
            qasm_text = qasm2_dumps(circuit)
            qasm_b64 = base64.b64encode(qasm_text.encode("utf-8")).decode("ascii")
            job_uid = self._submit_async(qasm_b64, shots)
            async_jobs.append({"job_uid": job_uid, "name": circuit.name, "shots": shots})

        return QuantagVMJob(
            backend=self,
            async_jobs=async_jobs,
            poll_interval=self.poll_interval,
            job_timeout=self.job_timeout,
        )
