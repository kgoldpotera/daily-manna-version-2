-- Enable uuid-ossp extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Churches table
CREATE TABLE churches (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pastors table (Multi-tenant via church_id)
CREATE TABLE pastors (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    church_id UUID REFERENCES churches(id) ON DELETE CASCADE,
    phone_number TEXT UNIQUE NOT NULL, -- Stored in E.164 format (e.g., 1234567890)
    admin_level INT DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Groups table
CREATE TABLE groups (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    church_id UUID REFERENCES churches(id) ON DELETE CASCADE,
    whatsapp_group_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Reading Plans table
CREATE TABLE reading_plans (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    day_number INT NOT NULL,
    scripture_text TEXT NOT NULL,
    reflection_question TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row-Level Security (RLS) on all tables
ALTER TABLE churches ENABLE ROW LEVEL SECURITY;
ALTER TABLE pastors ENABLE ROW LEVEL SECURITY;
ALTER TABLE groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE reading_plans ENABLE ROW LEVEL SECURITY;

-- Create default policies (for initial testing, you might want to adjust these for production)
CREATE POLICY "Allow read access to all" ON churches FOR SELECT USING (true);
CREATE POLICY "Allow read access to all" ON pastors FOR SELECT USING (true);
CREATE POLICY "Allow read access to all" ON groups FOR SELECT USING (true);
CREATE POLICY "Allow read access to all" ON reading_plans FOR SELECT USING (true);
