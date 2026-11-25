# Reproducible PICT workflow

The Lab06 workflow is intentionally limited to test-design artifacts; it does not implement the bank-transfer service.

## verify-lab.sh

1. Clones the official Microsoft PICT repository into a temporary directory outside this repository.
2. Builds PICT using CMake in Release mode.
3. Writes the source commit and CLI usage into results/pict-build.txt.
4. Runs browser 2-way, browser 3-way, transfer-nc, transfer, and transfer-neg without a random seed.
5. Calls validate-results.py to check model headers, tuple coverage, the nine constrained Category-Partition cases, and the one-negative-value rule.

## validate-results.py

Parses actual PICT output files. It checks all 2-way pairs for browser and transfer-nc, all 3-way tuples for browser, the complete expected nine-row constrained transfer model, and the PICT negative-testing invariant. It also selects three actual rows from transfer-neg for the README test-case table.

## finalize-readme.py

Reads the generated counts and selected rows and updates the marked README sections. It refuses to write a final report if required PICT evidence is missing or the generated constrained model does not have the expected nine rows.
