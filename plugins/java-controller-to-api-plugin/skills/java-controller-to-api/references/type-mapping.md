# Java ↔ TypeScript Type Mapping

## Primitive Types

| Java type | TypeScript type | Notes |
| :--- | :--- | :--- |
| `String` | `string` | |
| `Integer`, `Long`, `Short`, `BigInteger` | `number` | |
| `Double`, `Float`, `BigDecimal` | `number` | |
| `Boolean` | `boolean` | |
| `Character` | `string` | |
| `Void` | `void` | |
| `Object` | `any` | Avoid when possible; prefer concrete types |

## Date/Time Types

| Java type | TypeScript type | Notes |
| :--- | :--- | :--- |
| `LocalDate` | `string` | Format: YYYY-MM-DD |
| `LocalDateTime` | `string` | Format: YYYY-MM-DD HH:mm:ss |
| `OffsetDateTime` | `string` | ISO 8601 (with timezone) |
| `Date` | `string` | ISO 8601 |
| `Instant` | `string` | ISO 8601 |

## Collection Types

| Java type | TypeScript type | Notes |
| :--- | :--- | :--- |
| `List<E>`, `Set<E>` | `E[]` | |
| `Map<K, V>` | `Record<K, V>` | |
| `E[]` (array) | `E[]` | |
| `Optional<E>` | `E \| undefined` | Inside generated interfaces, emit `e?: E` instead |

## Spring-Specific Types

| Java type | TypeScript type | Notes |
| :--- | :--- | :--- |
| `MultipartFile` | `File` | For file uploads |
| `Page<T>` (Spring Data) | `PageResult<T>` | Requires the common type definitions below |
| `ResponseEntity<T>` | `T` | Unwrap the wrapper; return `T` directly |

## Generic Handling Rules

- Preserve generic structure: `Result<UserVO>` → `ApiResult<UserVO>`
- Nested generics: `PageResult<List<UserVO>>` → `PageResult<UserVO[]>`

## Custom Wrapper Types (Standard Responses)

Include the following base type definitions in the generated file when the endpoints use them:

```typescript
/** Standard API response wrapper */
export interface ApiResult<T = any> {
  code: number;
  message: string;
  data: T;
}

/** Paginated response structure */
export interface PageResult<T> {
  content: T[];
  totalElements: number;
  totalPages: number;
  size: number;
  number: number; // current page index (0-based)
}
```
