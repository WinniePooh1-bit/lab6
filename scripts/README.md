# Reproducible PICT workflow

The Lab06 workflow is limited to test-design artifacts; it does not implement the bank-transfer service.

## verify-lab.sh

1. Fetches the pinned official Microsoft PICT source commit into a temporary directory outside this repository.
2. Builds PICT with CMake in Release mode.
3. Writes the actual source commit and CLI usage to results/pict-build.txt.
4. Runs browser 2-way, browser 3-way, transfer-nc, transfer, and transfer-neg without a random seed.
5. Calls validate-results.py to check model headers, tuple coverage, the nine allowed Category-Partition combinations, their eight-row pairwise covering array, and the one-negative-value rule.

## validate-results.py

Parses the actual PICT output files. It checks every 2-way pair in browser and transfer-nc, every 3-way tuple in browser, all feasible pairs from the nine allowed transfer Category-Partition combinations, and the PICT negative-testing invariant. The constrained PICT array uses eight rows because one allowed tuple is redundant for pairwise coverage. It also selects three actual transfer-neg rows for the README test-case table.

## finalize-readme.py

Reads the generated counts and selected rows and updates the marked README sections. It refuses to write a final report if required PICT evidence is missing, if the nine allowed Category-Partition combinations are not represented in the model constraints, or if the eight-row pairwise array misses a feasible pair.
