require('dotenv').config();
const { Client, RemoteAuth } = require('whatsapp-web.js');
const { PostgresStore } = require('wwebjs-postgres');
const { Pool } = require('pg');
const qrcode = require('qrcode-terminal');
const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());

const WEBHOOK_URL = "http://localhost:8000/api/v1/webhook";
const PORT = 8001;
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || "daily_manna_secret_token_123";

console.log("Initializing whatsapp-web.js...");

if (!process.env.SUPABASE_DB_URL) {
    console.error("CRITICAL ERROR: SUPABASE_DB_URL is missing in environment variables. RemoteAuth requires it.");
    process.exit(1);
}

// Initialize Postgres connection pool for RemoteAuth
const pool = new Pool({
    connectionString: process.env.SUPABASE_DB_URL,
    ssl: { rejectUnauthorized: false } // Required for Supabase connections
});

const store = new PostgresStore({ pool: pool });

// Monkey-patch to fix a known bug in wwebjs-postgres where it expects the zip file in the root directory
const fs = require('fs');
const path = require('path');
const originalSave = store.save.bind(store);
store.save = async (options) => {
    const sessionName = options.session;
    // whatsapp-web.js saves the zip here:
    const actualZipPath = path.join('.wwebjs_auth', `${sessionName}.zip`);
    // wwebjs-postgres incorrectly looks for it here:
    const buggyExpectedPath = `${sessionName}.zip`;

    if (fs.existsSync(actualZipPath)) {
        fs.copyFileSync(actualZipPath, buggyExpectedPath);
    }
    
    try {
        await originalSave(options);
    } finally {
        if (fs.existsSync(buggyExpectedPath)) {
            fs.unlinkSync(buggyExpectedPath);
        }
    }
};

// Initialize the client
const client = new Client({
    authStrategy: new RemoteAuth({ 
        clientId: "CHURCH_BOT",
        store: store,
        backupSyncIntervalMs: 300000 // Sync to DB every 5 minutes
    }),
    puppeteer: {
        headless: true, // We can run headless because we will print the QR code to the terminal!
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    }
});

// Event: Log when session is backed up to DB
client.on('remote_session_saved', () => {
    console.log('✅ Remote Auth Session successfully backed up to Supabase database!');
});

// Generate QR Code in the terminal
client.on('qr', (qr) => {
    console.log('\n==================================================');
    console.log('📱 SCAN THIS QR CODE WITH YOUR WHATSAPP APP 📱');
    console.log('==================================================\n');
    qrcode.generate(qr, { small: true });
});

// Client is ready
client.on('ready', () => {
    console.log('\n✅ WhatsApp Web Client is Ready and Connected!');
});

// Listen for incoming messages
client.on('message', async message => {
    // Ignore status updates and WhatsApp Channels (Newsletters) to prevent AI spam
    if (message.from === 'status@broadcast' || message.from.includes('@newsletter')) {
        return;
    }
    
    let resolvedAuthor = message.author || message.from;
    
    // WhatsApp sometimes hides the real phone number behind a privacy "@lid" (Linked ID).
    // We must fetch the actual contact object to extract their real phone number!
    try {
        const contact = await message.getContact();
        // The real phone number is buried in contact.id.user, while contact.number holds the fake LID!
        if (contact && contact.id && contact.id.user) {
            resolvedAuthor = contact.id.user + "@c.us";
        } else if (contact && contact.number) {
            resolvedAuthor = contact.number + "@c.us";
        }
    } catch (err) {
        console.error("Failed to resolve real contact number:", err.message);
    }

    let hasQuotedMsg = Boolean(message.hasQuotedMsg || (message._data && message._data.quotedMsg));
    let quotedBody = "";
    let quotedAuthor = "";

    try {
        if (hasQuotedMsg) {
            if (message._data && message._data.quotedMsg) {
                quotedBody = message._data.quotedMsg.body || "";
                quotedAuthor = message._data.quotedMsg.author || message._data.quotedMsg.from || "";
            }
            try {
                const quoted = await message.getQuotedMessage();
                if (quoted) {
                    quotedBody = quoted.body || quotedBody;
                    quotedAuthor = quoted.author || quoted.from || quotedAuthor;
                }
            } catch (e) {
                // Keep fallback from _data.quotedMsg
            }
        }
    } catch (err) {
        console.error("Failed to fetch quoted message:", err.message);
    }
    
    try {
        // We structure the payload to match exactly what your FastAPI webhook expects
        await axios.post(WEBHOOK_URL, {
            event: "onMessage",
            data: {
                from: message.from,
                body: message.body,
                isGroupMsg: message.from.includes('@g.us'),
                author: resolvedAuthor,
                botNumber: client.info && client.info.wid ? client.info.wid.user : null,
                hasQuotedMsg: hasQuotedMsg,
                quotedBody: quotedBody,
                quotedAuthor: quotedAuthor,
                selectedButtonId: message.body.startsWith("broadcast_") || message.body === "cancel_broadcast" ? message.body : null
            }
        }, {
            headers: { "x-webhook-secret": WEBHOOK_SECRET }
        });
    } catch (e) {
        console.error("Failed to forward webhook to FastAPI:", e.message);
    }
});

// Listen for group join events (new member joins a WhatsApp group)
client.on('group_join', async (notification) => {
    try {
        const joinedUser = notification.recipientIds && notification.recipientIds.length > 0 
            ? notification.recipientIds[0] 
            : null;
        await axios.post(WEBHOOK_URL, {
            event: "onGroupJoin",
            data: {
                groupId: notification.chatId,
                joinedUser: joinedUser,
                botNumber: client.info && client.info.wid ? client.info.wid.user : null
            }
        }, {
            headers: { "x-webhook-secret": WEBHOOK_SECRET }
        });
    } catch (e) {
        console.error("Failed to forward group_join event to FastAPI:", e.message);
    }
});

// API Endpoint: Send Text
app.post('/api/sendText', async (req, res) => {
    const { chatId, text } = req.body;
    try {
        const result = await client.sendMessage(chatId, text);
        res.json({ success: true, result });
    } catch (e) {
        console.error("Send Text Error:", e);
        res.status(500).json({ success: false, error: e.message });
    }
});

// API Endpoint: Send Buttons
// Note: Meta recently blocked true interactive buttons on unofficial APIs.
// This endpoint automatically converts your buttons into a clean text-based menu that works 100% of the time!
app.post('/api/sendButtons', async (req, res) => {
    const { chatId, title, text, footer, buttons } = req.body;
    try {
        let menuText = title ? `*${title}*\n\n` : '';
        menuText += `${text}\n\n`;
        
        buttons.forEach((btn) => {
            // We ask the user to literally reply with the ID (e.g. broadcast_123)
            menuText += `👉 To select *${btn.text}*, reply with:\n${btn.id}\n\n`;
        });
        
        if (footer) menuText += `_${footer}_`;
        
        const result = await client.sendMessage(chatId, menuText);
        res.json({ success: true, result });
    } catch (e) {
        console.error("Send Buttons Error:", e);
        res.status(500).json({ success: false, error: e.message });
    }
});

app.get('/api/getBotInfo', (req, res) => {
    const botNumber = client.info && client.info.wid ? client.info.wid.user : null;
    res.json({ success: true, botNumber });
});

app.listen(PORT, () => {
    console.log(`🚀 Custom WhatsApp API Server listening on http://localhost:${PORT}`);
});


client.initialize();
