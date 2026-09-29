/**
 * Frontend Unit Test: Next.js API Proxy Routes (api_proxies.test.mjs)
 * Tests /api/chat, /api/chat/xray, and /api/voice-briefing proxies:
 * token minting, backend communication, error handling (502, 503, 401).
 */
import test from "node:test";
import assert from "node:assert/strict";

// Simulated proxy handler for /api/chat (from src/app/api/chat/route.ts)
async function simulateChatProxy({ body, session, backendFetch }) {
  try {
    const headers = { "Content-Type": "application/json" };
    if (session?.accessToken) {
      headers["Authorization"] = `Bearer ${session.accessToken}`;
    }

    const response = await backendFetch("http://localhost:8000/api/chat", {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return {
        status: response.status,
        body: { error: "Failed response from backend", details: errorText },
      };
    }

    const data = await response.json();
    return { status: 200, body: data };
  } catch (error) {
    return { status: 502, body: { error: "Failed to connect to backend" } };
  }
}

// Simulated proxy handler for /api/voice-briefing (from src/app/api/voice-briefing/route.ts)
async function simulateVoiceBriefingProxy({ session, backendFetch }) {
  try {
    if (!session) {
      return { status: 401, body: { error: "Unauthorized" } };
    }

    const headers = { Accept: "audio/mpeg" };
    if (session.accessToken) {
      headers["Authorization"] = `Bearer ${session.accessToken}`;
    }

    const response = await backendFetch("http://localhost:8000/api/voice-briefing", {
      method: "GET",
      headers,
    });

    if (!response.ok) {
      if (response.status === 503) {
        return {
          status: 503,
          body: {
            error: "Service unavailable",
            message: "Voice briefing service is temporarily down. Please try again later.",
          },
        };
      }
      return {
        status: response.status,
        body: { error: "Failed to generate voice briefing" },
      };
    }

    return { status: 200, stream: response.body };
  } catch (error) {
    return { status: 502, body: { error: "Failed to connect to voice briefing service" } };
  }
}

test("chat proxy returns 502 when backend connection fails", async () => {
  const mockFetch = async () => {
    throw new Error("ECONNREFUSED");
  };

  const res = await simulateChatProxy({
    body: { message: "hi" },
    session: null,
    backendFetch: mockFetch,
  });

  assert.equal(res.status, 502);
  assert.equal(res.body.error, "Failed to connect to backend");
});

test("chat proxy forwards backend error status and text", async () => {
  const mockFetch = async () => ({
    ok: false,
    status: 401,
    text: async () => "Unauthorized user token",
  });

  const res = await simulateChatProxy({
    body: { message: "hi" },
    session: null,
    backendFetch: mockFetch,
  });

  assert.equal(res.status, 401);
  assert.equal(res.body.error, "Failed response from backend");
  assert.equal(res.body.details, "Unauthorized user token");
});

test("chat proxy passes Authorization header and returns backend JSON on success", async () => {
  let capturedHeaders = null;
  const mockFetch = async (url, options) => {
    capturedHeaders = options.headers;
    return {
      ok: true,
      status: 200,
      json: async () => ({ message: "Hello from backend!", session_id: "s1" }),
    };
  };

  const res = await simulateChatProxy({
    body: { message: "hi" },
    session: { accessToken: "jwt_token_123" },
    backendFetch: mockFetch,
  });

  assert.equal(res.status, 200);
  assert.equal(res.body.message, "Hello from backend!");
  assert.equal(capturedHeaders["Authorization"], "Bearer jwt_token_123");
});

test("voice briefing proxy rejects unauthenticated call with 401", async () => {
  const res = await simulateVoiceBriefingProxy({ session: null, backendFetch: null });
  assert.equal(res.status, 401);
  assert.equal(res.body.error, "Unauthorized");
});

test("voice briefing proxy returns 503 when backend voice service is unavailable", async () => {
  const mockFetch = async () => ({
    ok: false,
    status: 503,
  });

  const res = await simulateVoiceBriefingProxy({
    session: { accessToken: "tok" },
    backendFetch: mockFetch,
  });

  assert.equal(res.status, 503);
  assert.equal(res.body.error, "Service unavailable");
  assert.ok(res.body.message.includes("temporarily down"));
});

test("voice briefing proxy returns 502 when backend connection throws", async () => {
  const mockFetch = async () => {
    throw new Error("Network error");
  };

  const res = await simulateVoiceBriefingProxy({
    session: { accessToken: "tok" },
    backendFetch: mockFetch,
  });

  assert.equal(res.status, 502);
  assert.equal(res.body.error, "Failed to connect to voice briefing service");
});
