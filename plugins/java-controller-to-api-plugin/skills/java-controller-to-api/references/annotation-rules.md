# Annotation Parsing and Conversion Rules

## 1. Validation Annotations → TypeScript Optionality

| Java annotation | TS behavior | Example |
| :--- | :--- | :--- |
| `@NotNull`, `@NotBlank`, `@NotEmpty` | **Required** (drop the `?`) | `username: string;` |
| No annotation / `@Null` | **Optional** (add `?`) | `email?: string;` |
| `@Valid` | Validate nested objects recursively | Nested objects follow the same rule |

## 2. Swagger/OpenAPI → JSDoc

Extract the following annotations as comments:

- **Class/interface comments**:
    - `@Schema(description = "...")` → JSDoc description
- **Field comments**:
    - `@Schema(description = "...", example = "...", requiredMode = ...)` → JSDoc
- **Method comments**:
    - `@Operation(summary = "...", description = "...")` → function JSDoc

### JSDoc generation example

```java
@Schema(description = "User ID", example = "1001")
@NotNull
private Long id;
```

```typescript
/**
 * User ID, example: 1001
 */
id: number;
```

## 3. Controller Route Parsing Rules

- **Concatenation rule**: class-level `@RequestMapping` + method-level mapping
- **BASE_URL**: extract the class-level `@RequestMapping` value into `const BASE_URL = '<path>'`, defined once directly above the API functions (use `''` when the class has no mapping). Every request URL must use `${BASE_URL}` (e.g. ``request.get(`${BASE_URL}/${id}`)``) instead of repeating the literal path.
- **Path parameters**: `@PathVariable("id")` → `${id}`
- **Query parameters**: `@RequestParam` → standalone parameters serialized as a shorthand config object (`{ status }`, `{ name, age }`)
- **Unannotated complex DTO (model attribute)** → serialize as query parameters (e.g. `request.get(BASE_URL, { query })`)
- **Request body**: `@RequestBody` → the function's body argument, named after the Java parameter (rename to `data` when the Java parameter name collides with `request`)

### Parameter naming rules

- Use the Java parameter name as-is.
- Never name a parameter `request` — it would shadow the mock request instance. Rename colliding parameters to `data`.

### Canonical call shapes

| HTTP method | Params present | Call shape |
| :--- | :--- | :--- |
| `GET` | none | `request.get(BASE_URL)` |
| `GET` | path only | ``request.get(`${BASE_URL}/${id}`)`` |
| `GET` | query (DTO or scalar) | `request.get(BASE_URL, { query })` |
| `POST`/`PUT` | `@RequestBody` | `request.post(BASE_URL, data)` |
| `PUT`/`PATCH`/`DELETE` | query params only (no body) | `request.put(BASE_URL, null, { status })` |

### API function naming conventions

Use the Java method name as-is, unless it does not already start with a verb matching its HTTP method — in that case apply the prefix conventions below:
- HTTP method mapping:
    - `GET` → `getXxx`, `fetchXxx`
    - `POST` → `createXxx`, `addXxx`
    - `PUT` → `updateXxx`
    - `DELETE` → `deleteXxx`, `removeXxx`
    - `PATCH` → `patchXxx`

### File upload handling

When a `MultipartFile` parameter is detected:

1. Set the TS parameter type to `File`.
2. Annotate the JSDoc with `FormData`.
3. Build the `FormData` object in the function body.

```typescript
/**
 * Upload user avatar
 * @param id User ID
 * @param file Avatar file (FormData)
 */
export function uploadAvatar(id: number, file: File): Promise<ApiResult<string>> {
  const formData = new FormData();
  formData.append('file', file);
  return request.post(`${BASE_URL}/${id}/avatar`, formData);
}
```

## 4. Enum Handling Rules

- **Forbidden**: generating TS `enum`.
- **Required**: generating string-literal union types.
- If the enum has `code` + `desc`, additionally generate a `Map` object.

```typescript
// Java: StatusEnum { ENABLED(1, "Enabled"), DISABLED(0, "Disabled") }

/** Status: 0-disabled, 1-enabled */
export type StatusEnum = 0 | 1;

export const StatusEnumMap = {
  0: 'Disabled',
  1: 'Enabled',
} as const;
```
