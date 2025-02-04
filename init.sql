-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "hstore";

-- Enable row-level security
ALTER DATABASE crumple SET row_security = on;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS netbox;
CREATE SCHEMA IF NOT EXISTS workboard;

-- Ensure workboard schema exists
CREATE SCHEMA IF NOT EXISTS workboard;

-- Drop and recreate tables to ensure clean state
DROP TABLE IF EXISTS workboard.users CASCADE;
DROP TABLE IF EXISTS workboard.device_roles CASCADE;

-- Create users table
CREATE TABLE workboard.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- Increased length to accommodate longer hashes
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert admin user if it doesn't exist
INSERT INTO workboard.users (username, password_hash, is_admin)
VALUES ('admin', 'scrypt:32768:8:1$BVKbea4jzS1la6rq$ba3d79a8f41bc8f500f104007b35a7c1a40232dcc96457b45cf8f34897960bd5360565d9e28e1d24369bdeb9e03d5668a8ad4a2927e143c225be8a75b8df4c50', true)
ON CONFLICT (username) DO NOTHING;


-- Create app settings table
CREATE TABLE workboard.app_settings (
    id SERIAL PRIMARY KEY,
    netbox_url VARCHAR(255) NOT NULL,
    netbox_token VARCHAR(255) NOT NULL,
    sync_interval INTEGER DEFAULT 300,
    is_connected BOOLEAN DEFAULT FALSE,
    last_sync TIMESTAMP WITH TIME ZONE,
    additional_config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Set up tables with appropriate indexes
CREATE TABLE workboard.clusters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    netbox_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(255),
    layout_data JSONB,
    meta_data JSONB,
    last_sync TIMESTAMP WITH TIME ZONE,
    sync_in_progress BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workboard.devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cluster_id UUID REFERENCES workboard.clusters(id) ON DELETE CASCADE,
    netbox_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    device_type VARCHAR(255),
    interfaces JSONB,
    position JSONB,
    meta_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workboard.connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cluster_id UUID REFERENCES workboard.clusters(id) ON DELETE CASCADE,
    device_a_id UUID REFERENCES workboard.devices(id) ON DELETE CASCADE,
    device_b_id UUID REFERENCES workboard.devices(id) ON DELETE CASCADE,
    interface_a VARCHAR(255),
    interface_b VARCHAR(255),
    meta_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create device roles table with predefined roles and colors
CREATE TABLE workboard.device_roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    color VARCHAR(7) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- Indexes
CREATE INDEX idx_clusters_netbox_id ON workboard.clusters(netbox_id);
CREATE INDEX idx_devices_cluster_id ON workboard.devices(cluster_id);
CREATE INDEX idx_devices_netbox_id ON workboard.devices(netbox_id);
CREATE INDEX idx_connections_cluster_id ON workboard.connections(cluster_id);

-- Add GiST index for JSONB fields
CREATE INDEX idx_devices_interfaces_gin ON workboard.devices USING gin (interfaces);
CREATE INDEX idx_clusters_layout_gin ON workboard.clusters USING gin (layout_data);

-- Update timestamp triggers
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_clusters_timestamp
    BEFORE UPDATE ON workboard.clusters
    FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_devices_timestamp
    BEFORE UPDATE ON workboard.devices
    FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_connections_timestamp
    BEFORE UPDATE ON workboard.connections
    FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_app_settings_timestamp
    BEFORE UPDATE ON workboard.app_settings
    FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_users_timestamp
    BEFORE UPDATE ON workboard.users
    FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

-- Function to hash existing tokens
CREATE OR REPLACE FUNCTION hash_existing_tokens()
RETURNS void AS $$
BEGIN
    UPDATE workboard.app_settings
    SET netbox_token = 'pbkdf2:sha256:600000$' || encode(sha256(netbox_token::bytea), 'hex')
    WHERE netbox_token IS NOT NULL
    AND netbox_token NOT LIKE 'pbkdf2:sha256:%';
END;
$$ LANGUAGE plpgsql;

-- Execute token hashing
SELECT hash_existing_tokens();
