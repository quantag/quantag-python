# solver.py
import pandas as pd

class QAOASolver:
    def __init__(self, backend="qiskit"):
        """
        backend: "qiskit" or "dwave"
        """
        self.backend = backend

    # -----------------------------
    # Data loading
    # -----------------------------
    def load_data(self, source, **kwargs):
        """Load data from CSV, Excel, or SQL connection string"""
        if source.endswith(".csv"):
            return pd.read_csv(source)
        elif source.endswith(".xlsx"):
            return pd.read_excel(source)
        elif source.startswith("postgresql://") or source.startswith("mysql://"):
            import sqlalchemy
            engine = sqlalchemy.create_engine(source)
            table = kwargs.get("table")
            return pd.read_sql_table(table, engine)
        else:
            raise ValueError(f"Unsupported source: {source}")

    # -----------------------------
    # Qiskit backend
    # -----------------------------
    def solve_with_qiskit(self, df):
        """Run portfolio optimization with Qiskit QAOA"""
        try:
            from qiskit_optimization import QuadraticProgram
            from qiskit_optimization.algorithms import MinimumEigenOptimizer
        except ImportError:
            raise ImportError("Install with: pip install qiskit qiskit-optimization")

        # Build Quadratic Program
        qp = QuadraticProgram()
        n = len(df)
        for i in range(n):
            qp.binary_var(name=f"x{i}")
        objective = {f"x{i}": df["returns"][i] for i in range(n)}
        qp.maximize(linear=objective)

        # Import QAOA (handle version differences)
        try:
            from qiskit.algorithms.minimum_eigensolvers import QAOA
        except ImportError:
            try:
                from qiskit_algorithms.minimum_eigensolvers import QAOA
            except ImportError:
                raise ImportError("QAOA not found. Run: pip install qiskit-algorithms")

        from qiskit.primitives import Sampler

        sampler = Sampler()
        qaoa = QAOA(sampler=sampler, reps=2)
        optimizer = MinimumEigenOptimizer(qaoa)
        result = optimizer.solve(qp)
        return result

    def solve_with_dwave(self, df, **kwargs):
        """
        Run portfolio optimization with D-Wave or local simulator.
        If no api_token is provided or solver access is unavailable,
        fall back to dimod.ExactSolver().
        """
        try:
            from dwave.system import DWaveSampler, EmbeddingComposite
            import dimod
        except ImportError:
            raise ImportError("Install with: pip install dwave-ocean-sdk")

        api_token = kwargs.get("api_token")
        endpoint = kwargs.get("endpoint", "https://cloud.dwavesys.com/sapi")
        solver_name = kwargs.get("solver")

        # Build QUBO: minimize -returns * x_i
        Q = {}
        for i, r in enumerate(df["returns"]):
            Q[(i, i)] = -r

        # Try cloud solver if token provided
        if api_token:
            try:
                if solver_name:
                    sampler = EmbeddingComposite(
                        DWaveSampler(
                            solver=solver_name,
                            client_kwargs={"token": api_token, "endpoint": endpoint},
                        )
                    )
                else:
                    sampler = EmbeddingComposite(
                        DWaveSampler(client_kwargs={"token": api_token, "endpoint": endpoint})
                    )
                return sampler.sample_qubo(Q, num_reads=100)
            except Exception as e:
                print(f"[Warning] D-Wave access failed ({e}). Falling back to local solver...")

        # Fallback: local classical solver
        sampler = dimod.ExactSolver()
        return sampler.sample_qubo(Q)




    # -----------------------------
    # Main API
    # -----------------------------
    def solve(self, source, problem="portfolio", **kwargs):
        """Solve an optimization problem"""
        df = self.load_data(source, **kwargs)

        if problem != "portfolio":
            raise ValueError("Only 'portfolio' problem type is implemented")

        if self.backend == "qiskit":
            return self.solve_with_qiskit(df)
        elif self.backend == "dwave":
            return self.solve_with_dwave(df, **kwargs)
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")

