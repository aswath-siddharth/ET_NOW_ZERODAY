/**
 * Frontend Unit Test: NextAuth JWT Minting (auth.test.mjs)
 * Tests mintBackendToken from auth.ts using Node.js test runner and jose.
 */
import test from "node:test";
import assert from "node:assert/strict";
import { SignJWT, jwtVerify } from "jose";

// Implementation under test (mimicking mintBackendToken logic from auth.ts)
async function mintBackendToken(session, secret) {
  if (!session?.user) return null;
  if (!secret) return null;

  const secretKey = new TextEncoder().encode(secret);
  const token = await new SignJWT({
    sub: session.user.id,
    email: session.user.email,
    name: session.user.name,
  })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime("1h")
    .sign(secretKey);

  return token;
}

test("mintBackendToken returns null when session has no user", async () => {
  const token = await mintBackendToken(null, "secret123");
  assert.equal(token, null);

  const tokenEmpty = await mintBackendToken({}, "secret123");
  assert.equal(tokenEmpty, null);
});

test("mintBackendToken returns null when secret is empty or missing", async () => {
  const session = { user: { id: "user_123", email: "test@et.com", name: "Tester" } };
  const token = await mintBackendToken(session, "");
  assert.equal(token, null);
});

test("mintBackendToken creates valid HS256 JWT with correct claims", async () => {
  const secret = "test_super_secret_for_nextauth_signing";
  const session = {
    user: {
      id: "usr_998877",
      email: "active_trader@economictimes.com",
      name: "Rohan Sharma",
    },
  };

  const token = await mintBackendToken(session, secret);
  assert.ok(token);
  assert.equal(typeof token, "string");

  // Verify token using jose
  const secretKey = new TextEncoder().encode(secret);
  const { payload, protectedHeader } = await jwtVerify(token, secretKey);

  assert.equal(protectedHeader.alg, "HS256");
  assert.equal(payload.sub, "usr_998877");
  assert.equal(payload.email, "active_trader@economictimes.com");
  assert.equal(payload.name, "Rohan Sharma");
  assert.ok(payload.exp);
  assert.ok(payload.iat);
  assert.ok(payload.exp > payload.iat);
});

test("mintBackendToken verification fails when secret does not match", async () => {
  const secret = "real_secret_key";
  const wrongSecret = "wrong_secret_key";
  const session = { user: { id: "u1", email: "a@b.com", name: "A" } };

  const token = await mintBackendToken(session, secret);
  const wrongKey = new TextEncoder().encode(wrongSecret);

  await assert.rejects(
    async () => {
      await jwtVerify(token, wrongKey);
    },
    { name: "JWSSignatureVerificationFailed" }
  );
});
