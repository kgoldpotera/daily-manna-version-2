const wa = require('@open-wa/wa-automate');
const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());

const WEBHOOK_URL = "http://localhost:8000/api/v1/webhook";
const PORT = 8001;
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || "daily_manna_secret_token_123";

wa.create({
  sessionId: "CHURCH_BOT",
  multiDevice: true, // Crucial for modern WhatsApp Web
  authTimeout: 0, // Disable auth timeout
  qrTimeout: 0, // Disable QR timeout
  headless: false, // Keep browser visible so you can click away popups
  useChrome: true,
  userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
  blockCrashLogs: true,
  disableSpins: true,
  hostNotificationLang: 'EN',
  logConsole: true,
}).then(client => start(client)).catch(err => {
    console.error("Failed to start OpenWA:", err);
});

function start(client) {
  console.log("✅ OpenWA Client Started Successfully!");

  // Forward incoming text messages
  client.onMessage(async message => {
    try {
      await axios.post(WEBHOOK_URL, {
        event: "onMessage",
        data: message
      }, {
        headers: { "x-webhook-secret": WEBHOOK_SECRET }
      });
    } catch (e) {
      console.error("Failed to forward webhook to FastAPI:", e.message);
    }
  });
  
  // Forward ANY message (e.g., button replies)
  client.onAnyMessage(async message => {
    // Avoid duplicate forwarding for normal chat messages
    if(message.type === 'chat') return; 
    
    try {
      await axios.post(WEBHOOK_URL, {
        event: "onAnyMessage",
        data: message
      }, {
        headers: { "x-webhook-secret": WEBHOOK_SECRET }
      });
    } catch (e) {
      console.error("Failed to forward button reply to FastAPI:", e.message);
    }
  });

  // FastAPI will call this to send text messages
  app.post('/api/sendText', async (req, res) => {
    const { chatId, text } = req.body;
    try {
      const result = await client.sendText(chatId, text);
      res.json({ success: true, result });
    } catch (e) {
      console.error("Send Text Error:", e);
      res.status(500).json({ success: false, error: e.message });
    }
  });

  // FastAPI will call this to send interactive button messages
  app.post('/api/sendButtons', async (req, res) => {
    const { chatId, title, text, footer, buttons } = req.body;
    try {
      const result = await client.sendButtons(chatId, text, buttons, title, footer);
      res.json({ success: true, result });
    } catch (e) {
      console.error("Send Buttons Error:", e);
      res.status(500).json({ success: false, error: e.message });
    }
  });

  app.listen(PORT, () => {
    console.log(`🚀 Custom OpenWA API Server listening on http://localhost:${PORT}`);
  });
}
