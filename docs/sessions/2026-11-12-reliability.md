# Session handoff — 2026-11-12

## Published changes

- Commit `f7493a8340678d0c7cd040bf2cd76cdba59ad660` adds bounded retries for transient dependency installation failures. Each installation phase has up to three attempts, a 150-second attempt limit and a five-second retry delay. Permanent package errors remain failures. The installation step has a ten-minute limit; the job limit is 35 minutes.
- The workflow now tests installer recovery before installation. The source list, crawler code, feed selection, schedules, permissions and concurrency configuration were not part of this commit. This file comparison is not a guarantee about future feed output.
- The news moderation workflow's delete-message handler was separately updated to retry transient deletion failures up to three times. An already-deleted message is treated as the requested final state. Persistent failures remain reported. Publication calls did not acquire retries.

## Evidence and limits

- [Failed run 43058423952](https://github.com/igor23740/ai-news-spider/actions/runs/43058423952) stopped during Playwright system dependency installation: Ubuntu package mirror names could not be resolved. The crawler did not start in that run.
- [Requested restart 43177842407](https://github.com/igor23740/ai-news-spider/actions/runs/43177842407) succeeded and saved ten RSS files in commit `7fabf323e6367f84d779b8f113b2d20116650ac9`. All ten files parsed as XML. Their item counts were retained; one Cursor link changed. The log's 76 articles across 38 configured sources is not a count of new news items.
- [Protection verification 43181339607](https://github.com/igor23740/ai-news-spider/actions/runs/43181339607) passed all six installer tests on GitHub and installed dependencies in 49 seconds. Its subsequent full crawl was unnecessary and was cancelled following the owner's correction. Final state: `cancelled`. Its feed commit step had not run; no feed update was published by this verification run.
- Local tests reproduced four failures with the previous installation commands; all six scenarios passed with the patch. Bash syntax, workflow YAML and the reverse patch were checked.
- The moderation patch passed nine local scenarios. Other 51 nodes, connections, settings and static data matched the pre-change snapshot. The publication database and outbox confirmed the new version. An authenticated empty callback completed on that version; it did not exercise a real Telegram deletion or induced connection reset.
- Cloudflare blocks for Perplexity, Midjourney and Ideogram appeared in both the preceding successful crawl and the requested restart. They are unresolved source-coverage issues; a successful overall job does not establish completeness.
- The first local test harness accidentally invoked real pip because only python was stubbed. Its output reported requirements already satisfied; no complete before/after inventory of the local Python environment was made. The corrected harness stubs both commands and excludes host package managers from its PATH.

## Rollback

The remote branch `backup/spider-pre-hardening-20261112` preserves commit `7fabf323e6367f84d779b8f113b2d20116650ac9`.

To remove only the installer protection, start from a fresh clean checkout of current main and revert the protection commit. Do not reset main to the backup, which would discard subsequent feed updates. Review the diff before pushing.

```bash
git revert f7493a8340678d0c7cd040bf2cd76cdba59ad660
```

The moderation workflow's full backup, patch/rollback tool and private evidence remain in the local, ignored `diag/review_2026-11-12/` directory. Do not force-add that directory: workflow exports contain credentials and operational data.

## Resume after the scheduled news delivery

1. Inspect the next normal GitHub run; do not trigger another full crawl just to check the installer.
2. Inspect the normal news workflow run and actual Telegram delivery. Its verified configured schedule is 00:02, 06:02, 12:02 and 18:02 Europe/Moscow. At handoff, the 12:02 run had not yet been verified. GitHub feed collection does not itself trigger this delivery workflow.
3. Check fresh deletion actions for persistent failures using existing executions. Do not create a paid news generation or test mailing without the owner's request.
4. Publisher remains unresolved: an identical Telegram post was submitted twice and generated the same unique site slug. The first article exists on the site. Ask the owner whether exact repeats should reuse one site article; that policy was not settled, and no publisher fix was deployed.

Use the session's clean worktree for continuation: `diag/review_2026-11-12/setup-worktree`, branch `fix/spider-setup-retry-20261112`. The original working directory has a pre-existing unstaged deletion of `.github/workflows/refresh.yml`; it was not included in the published changes.

Ask questions as ordinary chat messages, one concrete question at a time. For infrastructure changes, verify the changed stage separately and use the next scheduled run for full-pipeline observation where sufficient.
