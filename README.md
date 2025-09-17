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

Register at https://cloud.quantag-it.com/ and generate your API key at https://cloud.quantag-it.com/profile

Usage
-----

    from quantag.vm import QuantagVM
    from qiskit import QuantumCircuit

    backend = QuantagVM(api_key="<your API key>")
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    job = backend.run(qc, shots=1000)
    result = job.result()
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

