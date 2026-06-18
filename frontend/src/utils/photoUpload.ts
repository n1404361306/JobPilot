const MAX_FILE_SIZE = 2 * 1024 * 1024;
const MAX_DIMENSION = 400;
const ACCEPT_TYPES = ["image/jpeg", "image/png", "image/webp"];

export function isPhotoDataUrl(value?: string | null) {
  return Boolean(value?.startsWith("data:image/"));
}

export async function compressImageFile(file: File): Promise<string> {
  if (!ACCEPT_TYPES.includes(file.type)) {
    throw new Error("仅支持 JPG、PNG、WebP 格式");
  }
  if (file.size > MAX_FILE_SIZE) {
    throw new Error("图片不能超过 2MB");
  }

  const dataUrl = await readFileAsDataUrl(file);
  return resizeDataUrl(dataUrl, file.type === "image/png" ? "image/png" : "image/jpeg");
}

function readFileAsDataUrl(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error("图片读取失败"));
    reader.readAsDataURL(file);
  });
}

function loadImage(src: string) {
  return new Promise<HTMLImageElement>((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("图片解析失败"));
    image.src = src;
  });
}

async function resizeDataUrl(dataUrl: string, mimeType: string) {
  const image = await loadImage(dataUrl);
  const scale = Math.min(1, MAX_DIMENSION / Math.max(image.width, image.height));
  const width = Math.max(1, Math.round(image.width * scale));
  const height = Math.max(1, Math.round(image.height * scale));

  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext("2d");
  if (!context) {
    throw new Error("图片处理失败");
  }
  context.drawImage(image, 0, 0, width, height);
  return canvas.toDataURL(mimeType, mimeType === "image/jpeg" ? 0.85 : undefined);
}

export function dataUrlToImagePayload(dataUrl: string) {
  const match = dataUrl.match(/^data:(image\/(png|jpeg|jpg));base64,(.+)$/i);
  if (!match) {
    return null;
  }
  const type = match[2].toLowerCase() === "png" ? "png" : "jpg";
  const binary = atob(match[3]);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return { type, data: bytes } as const;
}
