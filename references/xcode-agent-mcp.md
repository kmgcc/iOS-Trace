# Xcode Coding Agents and MCP

Use when Xcode's project, build, test, or app-verification context may help investigate an iOS/iPadOS performance issue. This is an optional integration; Instruments traces remain the profiling evidence.

## Choose the right boundary

- Use the coding agent available in the host for repository inspection, edits, and coordination.
- If the agent exposes Xcode MCP tools, inspect the tool descriptions and permissions available in that session. Xcode and client capabilities vary by version.
- Use Xcode MCP for the Xcode actions it supports, such as project/build/test context or app verification. Use `xctrace` and Instruments for timelines, samples, hitches, allocations, power, and runtime attribution.
- Keep project test gates, signing, device ownership, user data, and physical-device rules in force when an MCP tool can perform an action.

## Xcode 27 MCP preview

Xcode 27 release notes describe a preview `xcrun mcp-server` experience that can run without an open workspace and can grant a code-signed agent access to projects under an approved directory tree. See [Apple's Xcode 27 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-27-release-notes), and check the installed release notes and help before relying on it.

Discover commands before use:

```text
xcrun mcp-server --help
xcrun mcp-server status
xcrun mcpbridge --help
```

The local help describes `mcpbridge` as the stdio entry point for Xcode MCP tools. Use the Agent client's current configuration instructions rather than copying a guessed configuration block. `mcp-server enable` requires administrator authorization and changes host-level settings. Do not enable, disable, approve agents, allow folders, or clear permissions as an implicit profiling step. Never use the preview's unsafe allow-all option for normal interactive development.

Do not assume a `start` subcommand or universal permission model. Use only the commands shown by the installed tool. Some settings may require relaunching Xcode or restarting the host. Enabling the server also does not automatically configure Codex, Antigravity, or another client.

## Apple-authored agent skills

Xcode 27 release notes describe exporting Apple's coding-agent skills for Codex when they are not available automatically. Check current Xcode documentation and `xcrun agent skills --help` before exporting; this is separate from iOS-Trace and should not overwrite an existing skill collection without reviewing the destination.
