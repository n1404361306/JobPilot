import { describe, expect, it } from "vitest";
import { decideRouteAccess } from "@/router";

describe("route access guard", () => {
  it("redirects guests away from authenticated routes", () => {
    const decision = decideRouteAccess({ requiresAuth: true }, false);

    expect(decision).toEqual({ name: "login", query: { redirect: "/" } });
  });

  it("redirects signed-in users away from guest-only routes", () => {
    const decision = decideRouteAccess({ guestOnly: true }, true);

    expect(decision).toEqual({ name: "dashboard" });
  });

  it("allows normal navigation when route meta matches session", () => {
    const decision = decideRouteAccess({ requiresAuth: true }, true);

    expect(decision).toBe(true);
  });
});
