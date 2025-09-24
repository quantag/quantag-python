from quantag import QAOASolver

solver = QAOASolver(backend="dwave")
result = solver.solve(
    "portfolio.csv",
    problem="portfolio",
    solver="Advantage_system4.1"
)
print(result)

