# Recording Storage and Recovery

Load this reference when a capture grows rapidly, Mac disk space drops, `xctrace` stays alive after its time limit, or storage does not return after recording. These checks apply to both physical iOS devices and Simulators: the target may be an iPhone or Simulator, but Instruments records and processes the trace on the Mac.

## Before recording

1. Identify the actual temporary and output volumes. Check `TMPDIR` and the output directory with `df -h`; create the output directory first if needed. `TMPDIR` is a starting point, not proof that every Instruments service uses it.
2. If this toolchain, template, device, or workload has not been measured on this Mac, begin with a short capture and observe free space and output growth. Set a reserve appropriate for the Mac and the expected capture; stop before either volume reaches it.
3. Treat `--time-limit` as a collection-time limit, not a byte cap or a guarantee that finalization completes promptly. Keep the recorder process under observation through finalization and set a reasonable deadline for the task.
4. `--output` selects the final `.trace` location. It does not guarantee that intermediate files or service caches use that volume. Setting `TMPDIR` may redirect some temporary files, but do not assume that it redirects `DTServiceHub` or other Instruments services. Verify actual open paths with `lsof` during a short capture before relying on an external disk to protect the internal disk.
5. Before a large export, check the export volume and narrow the time range, process, tables, or fields to the evidence needed. If a deleted-open `.ktrace` is still consuming space, diagnose it before starting another recording or large export.

## Inspect storage after each recording

After `xctrace record` exits, check the same volumes again:

```bash
df -h "${TMPDIR:-/tmp}" "/path/to/trace-output"
```

Then inspect files that have been unlinked but still have an open handle:

```bash
lsof -nP +c 0 +L1 2>/dev/null | grep -E 'DTServiceHub.*\.ktrace|\.ktrace.*DTServiceHub'
```

An empty result means this filter found no matching deleted-open `.ktrace`; it does not prove that all temporary files are gone. If space is still missing, inspect `df`, the sizes of the run's output and known temporary files, and other open files before acting. Record the path, size, PID, and command for any candidate.

For a matching PID, inspect its start time, executable, and command:

```bash
ps -p <PID> -o pid=,lstart=,command=
lsof -nP -p <PID> -d txt
```

Check for active `xctrace record` processes and Instruments GUI recordings before stopping `DTServiceHub`. A service can be shared with another recording; do not assume it belongs to the most recent task merely because its name matches.

## Decide what can be cleaned

- Preserve requested `.trace` bundles and exports. Do not remove an incomplete trace until its diagnostic value and retention are understood.
- A named intermediate file can be removed only after the recorder has exited, no process has it open, and evidence ties that exact path to the completed run. Inspect exact paths first; do not use a global `find ... -delete` or wildcard `rm` for `instruments*.ktrace`.
- Deleting a file does not release its blocks while a process still has it open. If `lsof +L1` shows a deleted `.ktrace`, closing the owning process's handle is what releases those blocks.
- For an exact `DTServiceHub` PID holding a deleted `.ktrace`, first confirm the executable and start time, confirm that no active Instruments recording depends on it, and confirm that the original recorder has exited. If the evidence is ambiguous or the service could belong to the user or another task, ask the user before stopping it.
- When the stale handle is clearly attributable to a completed run and no active session uses the service, send `SIGTERM` to that exact PID, wait, then rerun `lsof +L1` and `df -h` to verify release. Escalate to `SIGKILL` only for the same verified stale PID if it still holds the deleted file after `SIGTERM` and the task's process rules allow it. Never use `killall -9 DTServiceHub` as routine cleanup.
- The `com.apple.dt.InstrumentsCLI` cache is separate from deleted-open trace storage. Do not recursively delete the shared cache automatically. Inspect its exact size and contents, confirm no Instruments activity is using it, and ask before removing anything whose ownership or value is unclear.
- Do not kill the profiled app as a storage cleanup step. If a recording hangs or threatens the storage reserve, identify the exact `xctrace` process started for this run and stop that recorder according to the task's process rules; then inspect the service handles separately.

After any cleanup, rerun `lsof +L1` and `df -h` on the affected volume. Report the observed before/after free space and what was removed or stopped; a successful `rm` alone does not establish that storage was reclaimed.

## Recovery sequence

1. Stop starting new recordings or large exports while the affected volume is near its reserve.
2. Confirm the `xctrace` process for this run has exited. If it is still finalizing beyond the task's deadline, verify its PID and command before stopping only that recorder.
3. Inspect `lsof +L1`, identify the owning PID and exact deleted-open path, and check for other active Instruments sessions.
4. Decide whether an exact run-owned intermediate can be removed or whether a stale handle must be closed. Ask the user when ownership or impact is uncertain.
5. Verify the handle closed and free space returned with `lsof` and `df`. Preserve evidence and report any remaining growth or unresolved service state.
