import axios, { AxiosError, AxiosHeaders, type AxiosResponse, type InternalAxiosRequestConfig } from "axios";
import type { ApiEnvelope } from "./types";

export type TokenReader = () => string | null | undefined;

export function attachAuthHeader(
  config: InternalAxiosRequestConfig,
  readToken: TokenReader
): InternalAxiosRequestConfig {
  const token = readToken();
  config.headers = AxiosHeaders.from(config.headers);

  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }

  return config;
}

export function unwrapApiResponse<T>(payload: ApiEnvelope<T>): T {
  if (payload.code !== 0) {
    throw new Error(payload.message || "请求失败");
  }

  return payload.data;
}

export const http = axios.create({
  baseURL: "/api",
  timeout: 20000
});

let tokenReader: TokenReader = () => localStorage.getItem("jobpilot_access_token");
let unauthorizedHandler: (() => void) | null = null;

export function configureHttp(options: { readToken?: TokenReader; onUnauthorized?: () => void }) {
  if (options.readToken) {
    tokenReader = options.readToken;
  }

  if (options.onUnauthorized) {
    unauthorizedHandler = options.onUnauthorized;
  }
}

http.interceptors.request.use((config) => attachAuthHeader(config, tokenReader));

http.interceptors.response.use(
  (response: AxiosResponse<ApiEnvelope<unknown>>) =>
    unwrapApiResponse(response.data) as unknown as AxiosResponse<ApiEnvelope<unknown>>,
  (error: AxiosError<ApiEnvelope<unknown>>) => {
    const status = error.response?.status;
    const data = error.response?.data;

    if (status === 401 || data?.code === 4013 || data?.code === 4015) {
      unauthorizedHandler?.();
    }

    if (data?.message) {
      return Promise.reject(new Error(data.message));
    }

    return Promise.reject(error);
  }
);
