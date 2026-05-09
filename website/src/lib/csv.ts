import { readFile } from "fs/promises";
import path from "path";

export async function loadCsv<T = Record<string, string>>(
  publicPath: string,
): Promise<T[]> {
  const cleanPath = publicPath.replace(/^\/+/, "");
  const filePath = path.join(process.cwd(), "public", cleanPath);

  const text = await readFile(filePath, "utf-8");
  const [headerLine, ...lines] = text.trim().split(/\r?\n/);

  if (!headerLine) return [];

  const headers = headerLine.split(",").map((h) => h.trim());

  return lines
    .filter(Boolean)
    .map((line) => {
      const values = line.split(",").map((v) => v.trim());

      return headers.reduce<Record<string, string>>((row, header, index) => {
        row[header] = values[index] ?? "";
        return row;
      }, {}) as T;
    });
}