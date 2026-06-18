export function stripMarkdown(text: string): string {
  let result = text.replace(/```[\s\S]*?```/g, "");
  result = result.replace(/`([^`]+)`/g, "$1");
  result = result.replace(/\*\*([^*]+)\*\*/g, "$1");
  result = result.replace(/\*([^*]+)\*/g, "$1");
  result = result.replace(/^#{1,6}\s+/gm, "");
  result = result.replace(/^[-*+]\s+/gm, "");
  return result.replace(/\*\*/g, "").replace(/__/g, "").replace(/`/g, "").trim();
}
