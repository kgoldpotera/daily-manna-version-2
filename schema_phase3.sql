-- Part 1: Architecture Hardening

-- Add intercessor group ID to churches
ALTER TABLE churches ADD COLUMN IF NOT EXISTS intercessor_group_id TEXT;

-- Broadcast State Table
CREATE TABLE IF NOT EXISTS broadcast_state (
    phone_number TEXT PRIMARY KEY,
    message_text TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AI Chat History Table
CREATE TABLE IF NOT EXISTS ai_chat_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    phone_number TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Opt-Outs Table
CREATE TABLE IF NOT EXISTS opt_outs (
    phone_number TEXT PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Part 2: Phase 3 Features

-- Dynamic Lists Table
CREATE TABLE IF NOT EXISTS dynamic_lists (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    church_id UUID REFERENCES churches(id) ON DELETE CASCADE,
    list_type TEXT NOT NULL, -- 'pledge' or 'volunteer'
    member_number TEXT NOT NULL,
    amount_pledged NUMERIC,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Prayer Requests Table
CREATE TABLE IF NOT EXISTS prayer_requests (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    church_id UUID REFERENCES churches(id) ON DELETE CASCADE,
    original_sender TEXT NOT NULL,
    anonymized_text TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS and create permissive policies for local testing
ALTER TABLE broadcast_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE opt_outs ENABLE ROW LEVEL SECURITY;
ALTER TABLE dynamic_lists ENABLE ROW LEVEL SECURITY;
ALTER TABLE prayer_requests ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_policies WHERE policyname = 'Allow read access to all' AND tablename = 'broadcast_state') THEN
        CREATE POLICY "Allow read access to all" ON broadcast_state FOR ALL USING (true);
    END IF;
    IF NOT EXISTS (SELECT FROM pg_policies WHERE policyname = 'Allow read access to all' AND tablename = 'ai_chat_history') THEN
        CREATE POLICY "Allow read access to all" ON ai_chat_history FOR ALL USING (true);
    END IF;
    IF NOT EXISTS (SELECT FROM pg_policies WHERE policyname = 'Allow read access to all' AND tablename = 'opt_outs') THEN
        CREATE POLICY "Allow read access to all" ON opt_outs FOR ALL USING (true);
    END IF;
    IF NOT EXISTS (SELECT FROM pg_policies WHERE policyname = 'Allow read access to all' AND tablename = 'dynamic_lists') THEN
        CREATE POLICY "Allow read access to all" ON dynamic_lists FOR ALL USING (true);
    END IF;
    IF NOT EXISTS (SELECT FROM pg_policies WHERE policyname = 'Allow read access to all' AND tablename = 'prayer_requests') THEN
        CREATE POLICY "Allow read access to all" ON prayer_requests FOR ALL USING (true);
    END IF;
END
$$;
