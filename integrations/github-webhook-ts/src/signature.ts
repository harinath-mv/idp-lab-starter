// Day 20: the same HMAC-SHA256 check as app/security.py, in TypeScript.
import { createHmac, timingSafeEqual } from "node:crypto";

// What GitHub would send for this body and secret: "sha256=<hex>"
export function expectedSignature(secret: string, body: Buffer): string {
  const digest = createHmac("sha256", secret).update(body).digest("hex");
  return `sha256=${digest}`;
}

// true only if the header matches. `string | undefined`: the header may be missing.
export function isValidSignature(secret: string, body: Buffer, header: string | undefined): boolean {
  if (!secret || !header) {
    return false;
  }
  const expected = Buffer.from(expectedSignature(secret, body));
  const received = Buffer.from(header);
  // timingSafeEqual throws if lengths differ, so check length first (a wrong length is simply "no")
  if (expected.length !== received.length) {
    return false;
  }
  return timingSafeEqual(expected, received); // constant time, like hmac.compare_digest in Python
}
