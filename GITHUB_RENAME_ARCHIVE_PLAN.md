# GitHub Rename and Archive Plan

This is a reversible operator plan. No GitHub rename, archive, deletion, topic
change, default-branch change, or push was performed during migration.

## Rename candidate

### `feedback-analysis-system` → `feedback-intelligence-system`

Use the existing public repository identity and history. Do not create another
repository and do not force-push. Perform the rename only after the standalone
`migration/feedback-intelligence` branch and the FlowFoundry compatibility work
have been reviewed and pushed normally.

Operator sequence:

1. Review the local standalone migration branch and its CI configuration.
2. Push the branch normally and merge it using the repository's protected
   workflow; do not squash if preserving the prepared lineage is required.
3. Confirm legacy imports, commands, database paths/schema, Streamlit component
   IDs, exports, and redirects in the merged default branch.
4. Rename the existing GitHub repository in place.
5. Verify the old repository URL redirect, clone/fetch behavior, badges, Actions,
   Pages or deployment references, package metadata, and external links.
6. Update profile and FlowFoundry URLs in a separate, reversible documentation
   commit after the redirect is proven.

Rollback is an in-place rename back to the previous name plus reversion of only
the URL/documentation changes. History must not be rewritten.

## Retain, redirect, or archive candidates

| Repository or identity | Recommended state | Preconditions |
|---|---|---|
| `ai-workflow-foundry` | Active flagship | Push reviewed migration commits and verify CI |
| `ai-workspace-manager` | Temporary compatibility/release mirror | Keep active until FlowFoundry packaging and redirects are proven; archive only after explicit review |
| `confera-media-skills` | Public capability mirror or active component | Decide whether independent installation remains supported before any archive |
| `huiying-media-workbench` | Active private canonical product | Integrate reviewed private migration branch; never expose protected source |
| `huiying-desktop-release` | Private release/history mirror | Retain history and release assets; automate only after release-process approval |
| `feedback-analysis-system` | Rename in place | Complete compatibility and CI checks above |
| `grub-minimal-focus-theme` | Public side project, unpinned | Archive only if the owner wants a read-only side-project tier |
| `oppo-photo-archive` / `oppo-phone-control` | Supporting public utilities | Keep unpinned or secondary; never replace them with private operational trees |

Local legacy names such as `social-negative-monitor`, `meeting-media-auto`, and
`meeting-media-desktop` are migration/source identities, not instructions to
create new remote repositories.

## Archive safety checklist

- Make a verified local bundle first.
- Confirm the canonical replacement is public, documented, and CI-green.
- Add a clear redirect README where appropriate before archiving.
- Preserve tags, releases, issues, and package consumers.
- Treat archive as reversible read-only state, never deletion.
- Record the exact repository, old state, new state, date, and rollback owner.

