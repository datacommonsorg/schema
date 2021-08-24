# Data Commons Schema MCF Files

This directory contains the MCF nodes for all defined schemas in Data Commons.

These files are kept in-sync with the Google repository via Copybara:

-   Changes inside Google are immediately copied here.
-   Approved GitHub pull requests are sent to the Google respository, where it
    is tested; if approved, the PR will merge into both the Google and GitHub
    repository.
    -   IMPORTANT: DO NOT MERGE schema changes (any files ending with .mcf).
        Copybara will directly commit to the main branch then mark your PR as
        merged.

## Overview

- [schema.mcf](schema.mcf) contains MCF representation of Schema.org schemas.
- [dcschema.mcf](dcschema.mcf) contains general Data Commons classes and properties.
- [dcschema_enum_classes.mcf](dcschema_enum_classes.mcf) contains Data Commons enum classes.
- [dcschema_enum_instances.mcf](dcschema_enum_instances.mcf) contains Data Commons enum instances.
- [enum_specializations.mcf](enum_specializations.mcf) contains all enum `specializationOf`
  relationships.
  Please handle this file with care.
- [biomedical_schema](biomedical_schema) contains the Biomedical Data Commons (BMDC) domain
  specific schema.
- All other MCF files are source or domain specific.

## GitHub Development Process

In https://github.com/datacommonsorg/schema, click on "Fork" button to fork the
repo.

Clone your forked repo to your desktop.

Add datacommonsorg/schema repo as a remote:

```shell
git remote add dc https://github.com/datacommonsorg/schema.git
```

Every time when you want to send a Pull Request, do the following steps:

```shell
git checkout main
git pull dc main
git checkout -b new_branch_name
# Make some code change
git add .
git commit -m "commit message"
git push -u origin new_branch_name
```

Then in your forked repo, you can send a Pull Request. If this is your first
time contributing to a Google Open Source project, you may need to follow the
steps in [contributing.md](contributing.md).

Wait for approval of the Pull Request and merge the change.
