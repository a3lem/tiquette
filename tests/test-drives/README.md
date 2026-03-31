# Test Drives

High-level scenario scripts for manually exercising `tq` end-to-end.

Each `.md` file describes a realistic workflow. To run one, set up a temp
directory and point `TICKETS_DIR` at it:

```bash
export TICKETS_DIR=$(mktemp -d)/tickets
```

Then follow the steps. Clean up by removing the temp dir when done.
