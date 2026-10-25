# Keep only the Run all VS Code task

Goal: remove the old VS Code task entries and retain one working Bullet: Run all task.

Implementation steps:
1. Replace workspace tasks with a single process task that configures/builds the renderer and runs the existing flight launcher through uv.
2. Keep folder task lists empty and update the workspace task documentation.
3. Validate JSON, the shell command syntax, task count and launcher paths.

Interface changes: only Bullet: Run all remains in the configured task menu.
Scope/defaults: use the existing four-service launcher, shared locked uv environment, NVIDIA environment settings and existing configs. No launcher code, dependency changes or flight execution. Committing was subsequently authorized.
Verification: JSON parsing, single-task count, empty folder task lists, Bash syntax and launcher/build path checks passed. Flight and build were not launched.
Status: Implemented and verified. Folder task cleanup is committed; parent workspace task changes remain outside a Git repository.
Implementation commit: 28e1dc85dd1b0cd9f5339946a0f425532bb27735 (bullet_drone folder task cleanup). Parent workspace implementation commit: Pending.
