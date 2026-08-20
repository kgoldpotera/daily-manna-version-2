-- Phase 4: Users Table

CREATE TABLE IF NOT EXISTS users (
    phone_number TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_policies WHERE policyname = 'Allow read access to all' AND tablename = 'users') THEN
        CREATE POLICY "Allow read access to all" ON users FOR ALL USING (true);
    END IF;
END
$$;
