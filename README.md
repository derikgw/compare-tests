# compare-tests
Compare test facility for comparing an old (baseline) version of etl software output vs. newer (candidate) version of output.

The project includes a small hexagonal compare core that:

- checks out `main` as the default baseline, with support for tag or commit-hash overrides
- runs the baseline before the current workspace candidate
- reports schema additions and removals
- reports side-by-side baseline and candidate values for every column in each compared row
- supports excluded columns while still showing the full record and marking excluded fields in the report
