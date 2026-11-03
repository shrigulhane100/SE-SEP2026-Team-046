# Contributing Guidelines

Thank you for contributing! Follow these guidelines to keep work organized, changes easy to review, and the main branch stable.

## 1. Open and Assign an Issue

- The project manager creates an issue and assigns it to a developer before implementation begins.
- Each issue should include a clear description, expected behavior, acceptance criteria, and relevant screenshots or reproduction steps. Add priority and labels where appropriate.
- Check for existing issues to avoid duplicate work. Contributors may suggest improvements or report bugs; the project manager confirms scope and assignment.
- Clarify unclear requirements in the issue before starting. Record significant scope changes there.

## 2. Set Up the Repository

- Fork the repository into your GitHub account the first time you contribute, then clone your fork locally.
- Add the original repository as the `upstream` remote so you can keep your fork current.
- Follow the README for prerequisites, dependency installation, configuration, and running the project.
- Keep credentials in local configuration or environment variables. Never commit secrets, private keys, or local `.env` files.

The examples below use `OWNER/REPOSITORY` for the original project and `YOUR-USERNAME/REPOSITORY` for your fork. Replace these values before running the commands.

```bash
git clone https://github.com/YOUR-USERNAME/REPOSITORY.git
cd REPOSITORY
git remote add upstream https://github.com/OWNER/REPOSITORY.git
```

## 3. Create a Branch

Create a separate branch for each assigned issue, starting from the latest upstream `main`. Do not work directly on `main`.

Use a short, descriptive branch name that includes the type of change, issue number, and feature or fix:

- `feature/123-user-login`
- `fix/456-login-validation`
- `docs/789-update-setup-guide`
- `refactor/321-auth-service`

```bash
git fetch upstream
git switch main
git merge --ff-only upstream/main
git switch -c feature/123-user-login
```

If your local `main` has diverged, resolve that before creating the branch. Keep unrelated work in separate branches and pull requests.

## 4. Implement and Test

- Follow the project's existing architecture, naming conventions, formatting, and coding style.
- Keep changes focused on the assigned issue. Discuss major design changes or new dependencies before implementing them.
- Add or update tests for new behavior and bug fixes where appropriate, including relevant error cases.
- Run the applicable tests, formatter, linter, and build checks documented in the README or repository configuration.
- Update documentation, configuration examples, and migration instructions when behavior or setup changes.
- Avoid committing generated files, temporary files, logs, or unrelated formatting changes unless the project requires them.

## 5. Commit and Push

Write clear commit messages describing the change. Use a consistent format such as:

```text
feat: add user login
fix: reject invalid login input
docs: clarify local setup
```

Review your changes before committing, then push your branch to your fork:

```bash
git add <changed-files>
git commit -m "feat: add user login"
git push -u origin feature/123-user-login
```

## 6. Submit a Pull Request

Open a pull request from your fork's feature branch to the original repository's `main` branch. Use a draft pull request if you need early feedback or the work is incomplete.

Include the following in the pull request description:

- **Summary:** What changed and why.
- **Linked issue:** Use `Closes #123` for the issue this pull request fully resolves. For an issue in another repository, use `Closes OWNER/REPOSITORY#123`.
- **Validation:** Tests and checks performed, their results, and any checks you could not run.
- **Evidence:** Screenshots or recordings for visible UI changes, where applicable.
- **Impact:** Breaking changes, migrations, configuration changes, or known limitations.

Request review from the designated code reviewer. Ensure the pull request is focused, contains no secrets, and meets the issue's acceptance criteria.

## 7. Review and Merge

- The code reviewer checks correctness, readability, tests, security, and alignment with the issue requirements.
- The developer responds to feedback respectfully and pushes follow-up commits to the same branch. Resolve discussions after addressing the feedback or reaching agreement with the reviewer.
- If conflicts arise, update the branch with the latest upstream `main`, resolve the conflicts, and rerun relevant checks.
- An authorized reviewer or maintainer merges the pull request after required approvals and checks pass. Follow the repository's configured merge method.
- Do not bypass required reviews or merge a pull request with unresolved blocking feedback.

GitHub can automatically close a linked issue when a pull request containing a supported closing keyword, such as `Closes #123`, is merged into the repository's default branch. This workflow assumes `main` is the default branch. Use `Refs #123` when the change relates to an issue but does not fully resolve it.

After merging, verify that the issue is closed as intended, delete the completed feature branch, and sync your fork before starting the next task.

## Pull Request Checklist

- [ ] The issue is assigned to me and its scope is clear.
- [ ] My branch is based on the latest upstream `main`.
- [ ] My changes meet the acceptance criteria and follow project conventions.
- [ ] Relevant tests and checks pass; any exceptions are explained.
- [ ] Documentation and configuration examples are updated where needed.
- [ ] No secrets, temporary files, or unrelated changes are included.
- [ ] The pull request links the correct issue and explains the change.
- [ ] A designated reviewer has been requested.

## Security Reports

Do not report vulnerabilities or disclose credentials in public issues or pull requests. Follow `SECURITY.md` if available, or use GitHub's private vulnerability reporting when enabled. Otherwise, ask a maintainer for a private reporting channel without sharing sensitive details publicly.

## Communication and Conduct

Be respectful, constructive, and specific in issues and reviews. Follow `CODE_OF_CONDUCT.md` if present. Keep task decisions in the relevant issue or pull request so the team can follow the discussion. Notify the project manager if you are blocked or can no longer complete an assigned task.

## Maintainer Setup

Maintainers should configure protection rules for `main` to require pull requests, reviewer approval, and applicable status checks before merging. Keep setup and validation commands in the README current, and consider adding issue templates, a pull request template, `CODEOWNERS`, `SECURITY.md`, and `CODE_OF_CONDUCT.md` to make expectations clear.
