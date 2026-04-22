-- ============================================================
-- ROLES
-- ============================================================
CREATE ROLE app_user  NOLOGIN;
CREATE ROLE app_admin NOLOGIN;
-- BYPASSRLS дозволяє ігнорувати всі RLS-політики
CREATE ROLE app_service NOLOGIN BYPASSRLS;

-- Окремі логін-акаунти наслідують роль
CREATE USER regular_user PASSWORD 'secret' IN ROLE app_user;
CREATE USER admin_user   PASSWORD 'secret' IN ROLE app_admin;
CREATE USER service_bot  PASSWORD 'secret' IN ROLE app_service;

-- ============================================================
-- GRANTS
-- ============================================================
GRANT SELECT, INSERT, UPDATE, DELETE ON notes, reminders TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON notes, reminders, users TO app_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_service;

-- ============================================================
-- ROW LEVEL SECURITY (notes)
-- ============================================================
ALTER TABLE notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE notes FORCE ROW LEVEL SECURITY;   -- діє навіть на власника таблиці

-- app_user бачить лише свої нотатки
CREATE POLICY notes_user_isolation ON notes
    FOR ALL
    TO app_user
    USING (
        user_id = (
            SELECT id FROM users WHERE email = current_user
        )
    );

-- app_admin бачить усі нотатки
CREATE POLICY notes_admin_all ON notes
    FOR ALL
    TO app_admin
    USING (true);

-- app_service — не потребує політики: BYPASSRLS обходить RLS повністю

-- ============================================================
-- ROW LEVEL SECURITY (reminders)
-- ============================================================
ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminders FORCE ROW LEVEL SECURITY;

CREATE POLICY reminders_via_note ON reminders
    FOR ALL
    TO app_user
    USING (
        note_id IN (
            SELECT id FROM notes
            WHERE user_id = (
                SELECT id FROM users WHERE email = current_user
            )
        )
    );

CREATE POLICY reminders_admin_all ON reminders
    FOR ALL
    TO app_admin
    USING (true);

-- ============================================================
-- ПЕРЕВІРКА: чи може service_bot обходити RLS?
-- ============================================================
-- Підключитись як service_bot і виконати:
--
--   SET ROLE app_service;
--   SELECT * FROM notes;          -- поверне ВСІ рядки (BYPASSRLS)
--   RESET ROLE;
--
--   SET ROLE app_user;
--   SELECT * FROM notes;          -- поверне лише рядки поточного user_id
--   RESET ROLE;
--
-- Щоб переконатись що BYPASSRLS активний:
--   SELECT rolname, rolbypassrls FROM pg_roles WHERE rolname = 'app_service';
