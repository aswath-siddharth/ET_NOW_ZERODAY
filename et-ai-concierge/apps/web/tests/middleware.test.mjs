/**
 * Frontend Unit Test: Auth Middleware routing rules (middleware.test.mjs)
 * Tests route classification, public vs protected paths, redirection to /auth?callbackUrl=...
 */
import test from "node:test";
import assert from "node:assert/strict";

function evaluateMiddlewareRule(pathname, reqAuth, baseUrl = "http://localhost:3000") {
  const publicRoutes = ["/", "/auth", "/login", "/api/auth"];
  const isPublic = publicRoutes.some(
    (route) => pathname === route || pathname.startsWith(route + "/")
  );
  if (isPublic) return { action: "next" };

  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname.includes(".")
  ) {
    return { action: "next" };
  }

  if (!reqAuth) {
    const authUrl = new URL("/auth", baseUrl);
    authUrl.searchParams.set("callbackUrl", pathname);
    return { action: "redirect", url: authUrl.toString() };
  }

  return { action: "next" };
}

test("middleware allows public routes without session", () => {
  const publicPaths = ["/", "/auth", "/login", "/api/auth/signin", "/api/auth/callback/google"];
  for (const p of publicPaths) {
    const res = evaluateMiddlewareRule(p, null);
    assert.equal(res.action, "next", `Path ${p} should be permitted without auth`);
  }
});

test("middleware allows static assets and Next.js internals", () => {
  const staticPaths = ["/_next/static/chunks/main.js", "/favicon.ico", "/images/logo.png"];
  for (const p of staticPaths) {
    const res = evaluateMiddlewareRule(p, null);
    assert.equal(res.action, "next", `Static path ${p} should be allowed`);
  }
});

test("middleware redirects unauthenticated requests from protected routes", () => {
  const protectedPaths = ["/chat", "/dashboard", "/markets", "/marketplace", "/profile", "/onboarding"];
  for (const p of protectedPaths) {
    const res = evaluateMiddlewareRule(p, null);
    assert.equal(res.action, "redirect", `Protected path ${p} must redirect`);
    assert.ok(res.url.includes("/auth?callbackUrl="));
    assert.ok(res.url.includes(encodeURIComponent(p)) || res.url.includes(p));
  }
});

test("middleware allows authenticated requests through to protected routes", () => {
  const protectedPaths = ["/chat", "/dashboard", "/markets", "/marketplace", "/profile", "/onboarding"];
  const fakeSession = { user: { id: "u_1", email: "test@et.com" } };
  for (const p of protectedPaths) {
    const res = evaluateMiddlewareRule(p, fakeSession);
    assert.equal(res.action, "next", `Protected path ${p} should pass when authenticated`);
  }
});
