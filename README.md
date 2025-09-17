# QuantagVM

QuantagVM is a custom quantum simulator backend for Qiskit, 
developed as part of the Quantag Studio ecosystem.

It provides a minimal QVM (Quantum Virtual Machine) interface 
that can be used from Qiskit with one line of code. 
Later versions will integrate with CUDA-Q, MPI clusters, 
and the Quantag QBIN compiler.

------------------------------------------------------------

Installation
------------

    pip install quantag-vm

------------------------------------------------------------

Usage
-----

    from qiskit import QuantumCircuit, execute
    from quantag.vm import QuantagVM

    # Create a simple circuit
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()

    # Run it on QuantagVM
    backend = QuantagVM()
    result = execute(qc, backend, shots=100).result()

    print(result.get_counts())

------------------------------------------------------------

Project structure
-----------------

    quantag-vm/
        quantag/
            vm/
                backend.py
                __init__.py
                version.py
        tests/
            test_vm.py
        pyproject.toml
        README.md
        LICENSE

------------------------------------------------------------

License
-------

This project is licensed under the MIT License.

