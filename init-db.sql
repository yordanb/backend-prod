-- Initialize database: create app_user with limited privileges, and base roles
-- This runs automatically when MySQL container starts

-- Create application user with restricted privileges
CREATE USER IF NOT EXISTS 'app_user'@'%' IDENTIFIED BY 'app_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON testdb.* TO 'app_user'@'%';
FLUSH PRIVILEGES;

-- Verify admin (root) can access from any host (already exists)
-- Root user managed by MySQL image
