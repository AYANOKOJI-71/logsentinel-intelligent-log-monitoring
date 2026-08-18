export function percent(score: number): string {
  return `${Math.round(score * 100)}%`;
}

export function stamp(value: string): string {
  return new Intl.DateTimeFormat("en", { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(
    new Date(value),
  );
}
