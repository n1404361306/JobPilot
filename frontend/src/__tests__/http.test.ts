import axios from "axios";
import { describe, expect, it, vi } from "vitest";
import { attachAuthHeader, unwrapApiResponse } from "@/api/http";

describe("http helpers", () => {
  it("attaches bearer token to outgoing requests", () => {
    const config = attachAuthHeader(
      { headers: new axios.AxiosHeaders() },
      () => "abc-token"
    );

    expect(config.headers?.get("Authorization")).toBe("Bearer abc-token");
  });

  it("does not attach auth header when token is missing", () => {
    const config = attachAuthHeader(
      { headers: new axios.AxiosHeaders() },
      () => ""
    );

    expect(config.headers?.has("Authorization")).toBe(false);
  });

  it("unwraps successful backend envelope", () => {
    const data = unwrapApiResponse({ code: 0, message: "ok", data: { id: 1 } });

    expect(data).toEqual({ id: 1 });
  });

  it("throws backend message when business code is non-zero", () => {
    expect(() => unwrapApiResponse({ code: 4001, message: "bad", data: null })).toThrow("bad");
  });

  it("can build a client with provided unauthorized callback", () => {
    const onUnauthorized = vi.fn();
    const client = attachAuthHeader({ headers: new axios.AxiosHeaders() }, () => "token");

    onUnauthorized();

    expect(client.headers?.get("Authorization")).toBe("Bearer token");
    expect(onUnauthorized).toHaveBeenCalledTimes(1);
  });
});
