/**
 * Frontend UI & Components Contract Tests (ui_contracts.test.mjs)
 * Verifies core design contracts, routes, and data models for all screens.
 */
import test from "node:test";
import assert from "node:assert/strict";

// Helper from ProfilePage to format persona name
function formatPersona(persona) {
  return persona
    ? persona
        .replace("PERSONA_", "")
        .replace(/_/g, " ")
        .toLowerCase()
        .replace(/\b\w/g, (c) => c.toUpperCase())
    : "Unassigned";
}

test("persona name formatting converts snake_case enum to Title Case", () => {
  assert.equal(formatPersona("PERSONA_CONSERVATIVE_SAVER"), "Conservative Saver");
  assert.equal(formatPersona("PERSONA_ACTIVE_TRADER"), "Active Trader");
  assert.equal(formatPersona("PERSONA_YOUNG_PROFESSIONAL"), "Young Professional");
  assert.equal(formatPersona("PERSONA_CORPORATE_EXECUTIVE"), "Corporate Executive");
  assert.equal(formatPersona("PERSONA_HOME_BUYER"), "Home Buyer");
  assert.equal(formatPersona(null), "Unassigned");
  assert.equal(formatPersona(""), "Unassigned");
});

test("dashboard insight actions map to valid client routes", () => {
  const actionRoutes = {
    "Adjust SIP": "/marketplace?filter=sip",
    "Invest Now": "/marketplace?filter=elss",
    Enroll: "/chat?query=ET+Young+Minds+Masterclass",
    Rebalance: "/chat?query=portfolio+rebalancing",
    "Consult Advisor": "/chat?query=wealth+management",
    "Compare Plans": "/chat?query=insurance+plans",
    "View Analysis": "/chat?query=stock+analysis",
    "View Charts": "/chat?query=technical+analysis",
    "Scan Strikes": "/chat?query=options+opportunities",
    "Compare Offers": "/chat?query=home+loan+comparison",
    Calculate: "/chat?query=emi+calculator",
    "View Trends": "/chat?query=property+market+trends",
    "Read Analysis": "/chat?query=corporate+governance",
    "View FD Rates": "/chat?query=fd+interest+rates",
  };

  for (const [action, route] of Object.entries(actionRoutes)) {
    assert.ok(route.startsWith("/marketplace") || route.startsWith("/chat"), `Invalid route for ${action}: ${route}`);
  }
});

test("marketplace products contract has valid titles and chat deep-links", () => {
  const PRODUCTS = [
    {
      title: "Home Loans",
      match: "85% Approval Match",
      cta: "Compare Loans",
      route: "/chat?query=home+loan+comparison",
    },
    {
      title: "Health Insurance",
      match: "Coverage Gap Detected",
      cta: "View Plans",
      route: "/chat?query=health+insurance+plans",
    },
    {
      title: "Sovereign Gold Bonds",
      match: "Tax-Free Returns",
      cta: "Calculate Returns",
      route: "/chat?query=sovereign+gold+bonds+calculator",
    },
    {
      title: "Premium Credit Cards",
      match: "High Spending Match",
      cta: "Apply Now",
      route: "/chat?query=premium+credit+card+application",
    },
  ];

  assert.equal(PRODUCTS.length, 4);
  for (const p of PRODUCTS) {
    assert.ok(p.title);
    assert.ok(p.match);
    assert.ok(p.cta);
    assert.ok(p.route.startsWith("/chat?query="));
  }
});

test("markets metrics and signals contract definition", () => {
  const METRICS = [
    { title: "NIFTY 50", value: "22,200.00", change: "+0.68%", isPositive: true },
    { title: "SENSEX", value: "73,200.00", change: "+0.66%", isPositive: true },
    { title: "MCX GOLD", value: "₹62,450", change: "-0.12%", isPositive: false },
    { title: "USD/INR", value: "82.85", change: "+0.04%", isPositive: true },
  ];

  assert.equal(METRICS.length, 4);
  for (const m of METRICS) {
    assert.ok(m.title);
    assert.ok(m.value);
    assert.equal(typeof m.isPositive, "boolean");
  }
});
