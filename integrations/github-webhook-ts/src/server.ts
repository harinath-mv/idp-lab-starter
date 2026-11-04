// Day 20: start the Express app on a port (default 8001, so it can run next to the Python one on 8000).
import { createApp } from "./app.js";

const port = Number(process.env.PORT ?? 8001);
createApp().listen(port, () => {
  console.log(JSON.stringify({ ts: new Date().toISOString(), level: "INFO", msg: `listening on http://127.0.0.1:${port}` }));
});
