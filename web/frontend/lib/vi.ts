import dictionary from "./vi.json";

const messages: Record<string, string> = dictionary;
export function vi(value: string): string {
  return messages[value] ?? value;
}

// Translate presentation strings only. Source identifiers, numeric values and
// the original experiment protocol stay intact for reproducibility.
export function localizePayload<T>(value: T): T {
  function visit(node: unknown, key = ""): unknown {
    if (key === "protocol") return node;
    if (typeof node === "string") return vi(node);
    if (Array.isArray(node)) return node.map((item) => visit(item));
    if (node !== null && typeof node === "object") {
      return Object.fromEntries(
        Object.entries(node).map(([k, v]) => [k, visit(v, k)]),
      );
    }
    return node;
  }
  return visit(value) as T;
}
