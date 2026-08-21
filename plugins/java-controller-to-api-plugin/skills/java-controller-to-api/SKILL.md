---
name: java-controller-to-api
description: This skill should be used when the user asks to "generate frontend API", "convert Controller to TypeScript", "sync interface types", "generate API from a Controller", or requests syncing interface definitions after a Speckit task completes. Analyzes Java Spring Controllers and generates one single-file, self-contained TypeScript API module per Controller, with routes, HTTP methods, typed parameters/results, and JSDoc from Swagger annotations.
version: 0.1.0
---

# Java Controller → Frontend TypeScript API Generator

## Purpose

Analyze a Java Spring Boot Controller and generate a single, high-cohesion TypeScript API module for frontend consumption. Each Controller produces one `.ts` file that contains API functions, DTO/VO interfaces, enum types, and common wrapper types — complete and ready to compile.

## Core Principles

1. **Single-file output**: Generate one `.ts` file per Controller.
2. **Path completeness**: Concatenate the class-level `@RequestMapping` with method-level mappings.
3. **Type precision**: Follow `references/type-mapping.md` and `references/annotation-rules.md` strictly.
4. **Comment sync**: Convert Swagger/OpenAPI annotations into JSDoc.

## Workflow

### 1. Locate and read the Controller

- If the user specifies a file (e.g. `UserController.java`), read it with the Read tool.
- If not specified, use Glob to find `*Controller.java` files and let the user choose.
- Scan the Controller's imports for DTO/VO/enum dependencies and recursively read those files.

### 2. Parse the Controller

- **Base path**: Extract the class-level `@RequestMapping("/api/xxx")`.
- **Endpoints**: Iterate methods; extract `@GetMapping`, `@PostMapping`, etc.
- **Parameters**: Identify `@PathVariable`, `@RequestParam`, `@RequestBody`, and `MultipartFile`.
- **Return types**: Resolve generic wrappers such as `Result<T>` or `PageResult<T>`.

### 3. Generate the TypeScript file

Generate content in this exact order:

1. **File header**: Source Java file path and an auto-generated warning banner.
2. **Common types**: `ApiResult<T>` and `PageResult<T>` (only if used).
3. **Enums**: Convert Java enums to string-literal union types.
4. **DTO/VO interfaces**: All referenced request and response types.
5. **API functions**: Exported functions in Controller method order.

Name the file after the Controller class in camelCase minus the `Controller` suffix, plus `.api.ts` (`UserController` → `user.api.ts`).

Define `const BASE_URL = '<class-level @RequestMapping path>'` (`''` when absent) and the mock request instance `const request: any = {}` once per file, directly above the API functions. Use `${BASE_URL}` in every request URL. Never name a function parameter `request` — rename colliding Java parameters to `data`.

### 4. Verify

- Check whether a frontend directory exists (usually `frontend/src/api` or `src/api`).
- After generating, if `tsc` is available in the project, suggest running `tsc --noEmit` for a type check (suggestion only — do not force it).

## Interaction Rules

- **Output path confirmation**: In a Speckit flow, write the output to `specs/<current-task-directory>/types`. Otherwise use `frontend/src/api` or `src/api` if auto-detectable; if neither exists, ask the user: "Detected frontend directory at `frontend/src/api`. Generate there?"
- **Dependency resolution**: If a DTO references another unresolved DTO, resolve it recursively and generate it in the same file.

## Error Handling

- If a Java file has syntax errors, ask the user to fix the Java code first.
- If an unsupported complex generic is encountered, mark it `// TODO: verify this type manually` and continue generating the rest.

## References

Load these files as needed while parsing and generating:

- Type mapping rules: [references/type-mapping.md](references/type-mapping.md)
- Annotation parsing rules: [references/annotation-rules.md](references/annotation-rules.md)
- Complete input/output examples: [references/examples.md](references/examples.md)
