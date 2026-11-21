# MediaFlow public/private boundary

The FlowFoundry integration treats media paths and metadata as untrusted input.
Only portable relative paths may cross the public contract. The private product
resolves those values against its own configured root and retains responsibility
for symlink checks, immutable originals, non-overwriting output, storage,
provider configuration, and audit records.

Public examples are synthetic declarations and do not include media bytes.
Provider calls are not enabled by this contract. Confera Media Skills may
produce bounded proposals, but proposal review and export approval remain
separate gates owned by the host application.

The following classes of data are excluded from FlowFoundry:

- customer, student, meeting, or personnel media and metadata;
- user databases, task history, transcripts, and provider responses;
- credentials, cookies, tokens, certificates, signing keys, and password data;
- commercial, seller, legal-review, support, or supplier records;
- production endpoints, deployment state, and release artifacts.
