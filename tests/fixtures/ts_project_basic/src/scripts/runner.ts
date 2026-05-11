/**
 * Run migration jobs.
 * @param dryRun run mode
 */
export function runJobs(dryRun: boolean): number {
  return dryRun ? 0 : 1;
}
