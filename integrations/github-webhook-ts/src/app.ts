// Day 20: Express app with the GitHub webhook route (mirrors the Python receiver).
import express, { type Request, type Response } from "express";
import { isValidSignature } from "./signature.js";

// A TypeScript "interface" describes the shape of data: only the PR fields we use.
interface PullRequestEvent {
  action: string;
  pull_request: { number: number; title: string; user: { login: string } };
  repository: { full_name: string };
}

// Small JSON logger: one JSON object per line, like the Python service.
function log(level: string, msg: string, fields: Record<string, unknown> = {}): void {
  console.log(JSON.stringify({ ts: new Date().toISOString(), level, logger: "github-webhook-ts", msg, ...fields }));
}

export function createApp(getSecret: () => string = () => process.env.GITHUB_WEBHOOK_SECRET ?? "") {
  const app = express();

  app.get("/healthz", (_req: Request, res: Response) => {
    res.json({ status: "ok" });
  });

  // express.raw keeps the body as raw bytes (a Buffer). We MUST sign the raw bytes (Day 18, Ticket 1).
  app.post("/webhooks/github", express.raw({ type: "*/*", limit: "5mb" }), (req: Request, res: Response) => {
    const secret = getSecret();
    const deliveryId = req.get("x-github-delivery") ?? "";
    const event = req.get("x-github-event") ?? "";
    const body: Buffer = Buffer.isBuffer(req.body) ? req.body : Buffer.alloc(0);

    if (!secret) {
      log("ERROR", "GITHUB_WEBHOOK_SECRET is not set", { delivery_id: deliveryId });
      res.status(503).json({ detail: "webhook secret not configured" });
      return;
    }
    if (!isValidSignature(secret, body, req.get("x-hub-signature-256"))) {
      log("WARNING", "Rejected delivery: bad or missing signature", { delivery_id: deliveryId });
      res.status(401).json({ detail: "invalid signature" });
      return;
    }
    if (event === "ping") {
      res.json({ ok: true, event: "ping", message: "pong" });
      return;
    }
    if (event === "pull_request") {
      let pr: PullRequestEvent;
      try {
        pr = JSON.parse(body.toString("utf8")) as PullRequestEvent;
      } catch {
        res.status(422).json({ detail: "body is not valid JSON" });
        return;
      }
      if (typeof pr?.pull_request?.number !== "number") {
        res.status(422).json({ detail: "unexpected pull_request payload" });
        return;
      }
      log("INFO", `PR #${pr.pull_request.number} ${pr.action} in ${pr.repository.full_name}`, {
        delivery_id: deliveryId,
        event,
      });
      res.json({
        ok: true,
        event,
        action: pr.action,
        repo: pr.repository.full_name,
        number: pr.pull_request.number,
        title: pr.pull_request.title,
      });
      return;
    }
    res.json({ ok: true, event, ignored: true });
  });

  return app;
}
