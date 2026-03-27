const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');
const app = express();

app.use(express.json());

// ============================================
// WhatsApp Client Setup
// ============================================

const client = new Client({
    authStrategy: new LocalAuth({ clientId: "afaq-bot" }),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu'
        ]
    }
});

let isReady = false;
let botStatus = 'starting';

// ============================================
// Event Handlers
// ============================================

client.on('qr', (qr) => {
    console.log('\n========================================');
    console.log('SCAN THIS QR CODE WITH YOUR PHONE:');
    console.log('========================================\n');
    qrcode.generate(qr, { small: true });
    console.log('\n========================================');
    console.log('Scan with WhatsApp > Linked Devices');
    console.log('========================================\n');
    botStatus = 'waiting_for_qr';
});

client.on('authenticated', () => {
    console.log('✅ Authenticated!');
    botStatus = 'authenticated';
});

client.on('auth_failure', (msg) => {
    console.error('❌ Auth failure:', msg);
    botStatus = 'auth_failed';
});

client.on('ready', () => {
    console.log('✅ WhatsApp Bot Ready!');
    console.log('Phone:', client.info.wid.user);
    isReady = true;
    botStatus = 'ready';
});

client.on('disconnected', (reason) => {
    console.log('❌ Disconnected:', reason);
    isReady = false;
    botStatus = 'disconnected';
    client.initialize();
});

// ============================================
// Message Handler - Forward to Python
// ============================================

client.on('message', async (msg) => {
    // Skip own messages and status updates
    if (msg.fromMe || msg.isStatus) return;
    
    // Skip group messages
    const chat = await msg.getChat();
    if (chat.isGroup) return;

    console.log(`📩 ${msg.from}: ${msg.body}`);

    try {
        // Forward to Python webhook
        const response = await fetch('http://localhost:8000/api/whatsapp/webhook', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                from: msg.from,
                body: msg.body,
                type: msg.type,
                timestamp: msg.timestamp,
                pushname: msg._data.notifyName || 'Guest'
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.reply) {
                await msg.reply(data.reply);
                console.log(`📤 Reply sent to ${msg.from.slice(-4)}`);
            }
        }
    } catch (err) {
        console.error('Webhook error:', err.message);
        
        // Fallback reply
        await msg.reply('مرحبا! شكراً لرسالتك. سأعود إليك قريباً.\nHello! Thanks for your message. I\'ll get back to you soon.');
    }
});

// ============================================
// API Endpoints
// ============================================

// Health check
app.get('/health', (req, res) => {
    res.json({
        status: botStatus,
        ready: isReady,
        phone: client.info?.wid?.user || null
    });
});

// Send message
app.post('/send', async (req, res) => {
    if (!isReady) {
        return res.status(503).json({ error: 'Bot not ready' });
    }

    try {
        const { to, message } = req.body;
        let chatId = to.includes('@c.us') ? to : `${to.replace(/[^0-9]/g, '')}@c.us`;
        
        const sent = await client.sendMessage(chatId, message);
        res.json({
            status: 'sent',
            id: sent.id._serialized
        });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Get chats
app.get('/chats', async (req, res) => {
    if (!isReady) {
        return res.status(503).json({ error: 'Bot not ready' });
    }

    try {
        const chats = await client.getChats();
        res.json({
            total: chats.length,
            chats: chats.slice(0, 20).map(c => ({
                name: c.name,
                id: c.id._serialized,
                unread: c.unreadCount,
                lastMessage: c.lastMessage?.body?.slice(0, 50)
            }))
        });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Get contact info
app.get('/contact/:phone', async (req, res) => {
    if (!isReady) {
        return res.status(503).json({ error: 'Bot not ready' });
    }

    try {
        const phone = req.params.phone.replace(/[^0-9]/g, '');
        const contact = await client.getContactById(`${phone}@c.us`);
        res.json({
            name: contact.pushname || contact.name,
            number: contact.number,
            isBusiness: contact.isBusiness
        });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ============================================
// Start Server
// ============================================

const PORT = 3000;
app.listen(PORT, () => {
    console.log(`\n🚀 WhatsApp Bridge running on port ${PORT}`);
    console.log(`   API: http://localhost:${PORT}`);
    console.log(`   Health: http://localhost:${PORT}/health`);
    console.log('\nInitializing WhatsApp client...\n');
});

// Initialize WhatsApp
client.initialize();
