import path from "path";

export function repoFile(...parts: string[]): string[] {
  const cwd = process.cwd();
  return [
    path.resolve(cwd, "..", ...parts),
    path.resolve(cwd, ...parts),
  ];
}
