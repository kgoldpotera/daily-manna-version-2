# Daily Manna WhatsApp Bot

A WhatsApp bot that sends daily Bible readings and helps users track their spiritual journey.

## Features

- 📖 Daily Bible reading plan (365 days)
- ⏰ Customizable daily reminders
- 📊 Reading progress tracking
- 💭 Reflection journaling
- 📱 Multiple Bible versions (ESV, NIV, KJV)
- 🔗 Direct links to online Bible readings

## Setup

### 1. Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:
- `ULTRAMSG_INSTANCE_ID` - Your UltraMsg instance ID
- `ULTRAMSG_TOKEN` - Your UltraMsg API token
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon key

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Generate Reading Plan

```bash
python reading_plan_generator.py
```

### 4. Database Setup

Create these tables in your Supabase database:

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reminder_time TEXT DEFAULT '07:00',
    reminder_active BOOLEAN DEFAULT true,
    preferred_version TEXT DEFAULT 'ESV',
    timezone TEXT DEFAULT 'UTC'
);

-- Progress table
CREATE TABLE progress (
    id SERIAL PRIMARY KEY,
    user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
    days_completed INTEGER DEFAULT 0,
    current_day INTEGER DEFAULT 1,
    last_read_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Reflections table
CREATE TABLE reflections (
    id SERIAL PRIMARY KEY,
    user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
    reflection TEXT NOT NULL,
    day INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 5. Run the Application

Start the API server:
```bash
python -m app.main
```

Start the reminder scheduler (in a separate terminal):
```bash
python run_scheduler.py
```

## WhatsApp Commands

### Getting Started
- `START` - Register for Daily Manna
- `HELP` - Show all available commands

### Reading & Progress
- `TODAY` - Get today's Bible reading
- `READ` - Mark today's reading as complete
- `STATS` - View your reading progress
- `REFLECT <your thoughts>` - Save a reflection

### Reminders
- `REMIND 7:00` - Set daily reminder time
- `6:30 AM` - Set reminder time (alternative format)
- `STOP REMINDER` - Turn off daily reminders

### Bible Versions
- `ESV` - Set Bible version to ESV
- `NIV` - Set Bible version to NIV
- `KJV` - Set Bible version to KJV

### Other
- `RESET` - Reset all your data (for testing)

## API Endpoints

- `GET /` - Health check
- `POST /webhook` - WhatsApp webhook
- `GET /today-reading` - Get today's reading
- `GET /reading/{day}` - Get reading for specific day
- `GET /join` - Redirect to WhatsApp

## Deployment

### Using Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set environment variables in Render dashboard
4. Deploy!

### Using Railway

1. Connect your GitHub repository to Railway
2. Set environment variables
3. Deploy the main API
4. Deploy the scheduler as a separate service

## Project Structure

```
app/
├── __init__.py
├── main.py              # FastAPI application
├── config.py            # Configuration settings
├── api/
│   └── routes.py        # API routes
├── database/
│   └── client.py        # Database connection
├── models/
│   └── user.py          # Data models
├── services/
│   ├── user_service.py      # User management
│   ├── bible_service.py     # Bible reading logic
│   ├── whatsapp_service.py  # WhatsApp integration
│   └── message_handler.py   # Message processing
└── scheduler/
    └── reminder_scheduler.py # Daily reminders

reading_plan.json        # 365-day reading plan
run_scheduler.py         # Scheduler runner script
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details.