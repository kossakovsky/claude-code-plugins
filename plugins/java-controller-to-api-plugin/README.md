# java-controller-to-api-plugin

Generate frontend TypeScript API modules from Java Spring Controllers.

## Overview

This plugin provides the `java-controller-to-api` skill: analyze a Java Spring Boot `@RestController` and generate a single, self-contained TypeScript file containing:

- **API functions** with fully concatenated routes (class-level `@RequestMapping` + method-level mappings) and HTTP methods
- **A shared `BASE_URL` constant** holding the Controller's class-level path, referenced by every endpoint
- **Typed parameters and results** — `@PathVariable`, `@RequestParam`, `@RequestBody`, `MultipartFile`, generic wrappers (`Result<T>`, `PageResult<T>`)
- **DTO/VO interfaces** and **string-literal union types** for enums, recursively resolved from imports
- **JSDoc comments** derived from Swagger/OpenAPI annotations (`@Operation`, `@Schema`)

## Installation

### Local directory

```bash
claude --plugin-dir /path/to/java-controller-to-api-plugin
```

Or add to your `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {},
  "enabledPlugins": {}
}
```

### Marketplace

*To be published — see "Publishing" below.*

## Usage

The skill activates automatically. Just describe the task in natural language:

- "Generate the frontend API for `UserController.java`"
- "Sync interface types after this Speckit task"
- "Convert this Controller to TypeScript"

Claude will:

1. Locate the Controller (or list `*Controller.java` files for you to choose)
2. Recursively read its DTO/VO/enum dependencies
3. Generate the `.ts` file into `frontend/src/api` or `src/api` (auto-detected; asks when ambiguous)

## Skill Details

| Skill | Purpose |
|-------|---------|
| `java-controller-to-api` | Parse a Spring Controller and generate a single-file TypeScript API module |

Reference docs bundled with the skill:

- `references/type-mapping.md` — Java → TypeScript type mapping rules
- `references/annotation-rules.md` — annotation parsing and conversion rules
- `references/examples.md` — full input/output examples and Speckit integration

## Requirements

- A Java Spring Boot project (Controllers with Spring MVC annotations)
- A frontend directory where generated files land (`frontend/src/api` or `src/api`)
- Optional: `tsc` available for post-generation type checking

## Publishing

This plugin is published on the [cc-plugins community marketplace](https://github.com/kossakovsky/cc-plugins). The source repository is <https://github.com/gk7261234/AISkill>.

Marketplace entry format:

```json
{
  "name": "java-controller-to-api-plugin",
  "description": "Generate frontend TypeScript API modules from Java Spring Controllers",
  "version": "0.1.0",
  "author": { "name": "gk7261234" },
  "source": "./plugins/java-controller-to-api-plugin",
  "category": "developer-tools",
  "tags": ["java", "spring", "typescript", "api", "codegen"]
}
```

## License

MIT
