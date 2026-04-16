---
title: Modules & Interfaces
permalink: /en/interface_reference
desc: High-level structure of the system modules, interface constraints, and entry points to sub-documents.
breadcrumb: Modules & Interfaces
layout: default
---

## Reading Guide

This section is meant to answer two questions:

1. What major module groups exist in the repository?
2. What interface constraints should stay stable across implementations?

## Main Categories

- [Architecture]({{ '/en/architecture' | relative_url }})
- [Drivers]({{ '/en/driver_overview' | relative_url }})
- [LIO]({{ '/en/lio_overview' | relative_url }})
- [Localization]({{ '/en/localization_overview' | relative_url }})
- [Auto Aim]({{ '/en/rm_auto_aim' | relative_url }})
- [System Integration]({{ '/en/integration_overview' | relative_url }})
- [Topic Reference]({{ '/en/topics' | relative_url }})
- [TF Tree]({{ '/en/tf_tree' | relative_url }})

## Core Principle

Different algorithms may be replaced over time, but the surrounding contracts should remain predictable:

- input topics
- output topics
- TF responsibilities
- naming conventions
- startup entry points
