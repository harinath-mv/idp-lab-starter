// Day 20: the same "what if" tests as Day 18, with Node's built-in test runner.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import request from "supertest";
import { createApp } from "../src/app.js";
import { expectedSignature, isValidSignature } from "../src/signature.js";

const SECRET = "test-secret-123";
// Same sample event as the Python tests, so both languages are checked against identical bytes.
const PAYLOAD = readFileSync(new URL("../../github-webhook/tests/payloads/pull_request_opened.json", import.meta.url));

const app = createApp(() => SECRET);

function send(body: Buffer, signature: string | null, event = "pull_request") {
  const req = request(app)
    .post("/webhooks/github")
    .set("Content-Type", "application/json")
    .set("X-GitHub-Event", event)
    .set("X-GitHub-Delivery", "ts-test-1");
  if (signature !== null) {
    req.set("X-Hub-Signature-256", signature);
  }
  // Send the exact bytes as text. (Passing a Buffer with a JSON content type makes the
  // test client re-encode it, which changes the bytes and breaks the signature: Day 18 lesson.)
  return req.send(body.toString("utf8"));
}

test("same signature as the Python service for the same bytes", () => {
  // Python: hmac.new(b"test-secret-123", b"hello", hashlib.sha256).hexdigest()
  assert.equal(
    expectedSignature(SECRET, Buffer.from("hello")),
    "sha256=47e6180a0438c2a36267116d1a5398ad7b00848df0dfa53867545b3d0173beb5",
  );
});

test("valid signature is accepted and parsed", async () => {
  const res = await send(PAYLOAD, expectedSignature(SECRET, PAYLOAD));
  assert.equal(res.status, 200);
  assert.equal(res.body.number, 42);
  assert.equal(res.body.repo, "harinath-mv/idp-lab-starter");
});

test("wrong signature is rejected", async () => {
  const res = await send(PAYLOAD, "sha256=" + "0".repeat(64));
  assert.equal(res.status, 401);
});

test("missing signature is rejected", async () => {
  const res = await send(PAYLOAD, null);
  assert.equal(res.status, 401);
});

test("short or malformed signature is rejected without crashing", async () => {
  const res = await send(PAYLOAD, "sha256=abc");
  assert.equal(res.status, 401);
});

test("tampered body is rejected", async () => {
  const tampered = Buffer.from(PAYLOAD.toString("utf8").replace('"opened"', '"closed"'));
  const res = await send(tampered, expectedSignature(SECRET, PAYLOAD));
  assert.equal(res.status, 401);
});

test("no secret configured fails closed", async () => {
  const res = await request(createApp(() => ""))
    .post("/webhooks/github")
    .set("Content-Type", "application/json")
    .set("X-Hub-Signature-256", expectedSignature(SECRET, PAYLOAD))
    .send(PAYLOAD.toString("utf8"));
  assert.equal(res.status, 503);
});

test("ping is answered", async () => {
  const body = Buffer.from('{"zen":"Keep it logically awesome."}');
  const res = await send(body, expectedSignature(SECRET, body), "ping");
  assert.equal(res.status, 200);
  assert.equal(res.body.message, "pong");
});

test("isValidSignature handles undefined header", () => {
  assert.equal(isValidSignature(SECRET, Buffer.from("x"), undefined), false);
});
