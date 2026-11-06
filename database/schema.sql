PRAGMA foreign_keys = ON;

CREATE TABLE students (
    id          INTEGER NOT NULL PRIMARY KEY,
    student_no  VARCHAR(32) NOT NULL,
    name        VARCHAR(32) NOT NULL,
    role        VARCHAR(16) NOT NULL DEFAULT '学生',
    active      BOOLEAN NOT NULL DEFAULT 1,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_students_student_no UNIQUE (student_no),
    CONSTRAINT ck_students_role CHECK (role IN ('学生', '班长', '教师')),
    CONSTRAINT ck_students_no_len CHECK (length(student_no) BETWEEN 6 AND 32),
    CONSTRAINT ck_students_name_len CHECK (length(name) BETWEEN 1 AND 32)
);

CREATE INDEX idx_students_active_no ON students (active, student_no);

CREATE TABLE rollcall_sessions (
    id          INTEGER NOT NULL PRIMARY KEY,
    title       VARCHAR(64) NOT NULL,
    status      VARCHAR(16) NOT NULL DEFAULT 'calling',
    order_by    VARCHAR(16) NOT NULL DEFAULT 'student_no',
    started_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at    DATETIME,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_sessions_status CHECK (status IN ('calling', 'ended')),
    CONSTRAINT ck_sessions_order_by CHECK (order_by IN ('student_no', 'name', 'id')),
    CONSTRAINT ck_sessions_title_len CHECK (length(title) BETWEEN 1 AND 64),
    CONSTRAINT ck_sessions_time CHECK (ended_at IS NULL OR ended_at >= started_at),
    CONSTRAINT ck_sessions_state CHECK (
        (status = 'calling' AND ended_at IS NULL)
        OR (status = 'ended' AND ended_at IS NOT NULL)
    )
);

CREATE INDEX idx_sessions_started ON rollcall_sessions (started_at, id);
CREATE INDEX idx_sessions_status ON rollcall_sessions (status);

CREATE TABLE attendance_records (
    id            INTEGER NOT NULL PRIMARY KEY,
    session_id    INTEGER NOT NULL,
    student_id    INTEGER NOT NULL,
    student_no    VARCHAR(32) NOT NULL,
    student_name  VARCHAR(32) NOT NULL,
    role          VARCHAR(16) NOT NULL,
    order_no      INTEGER NOT NULL,
    status        VARCHAR(16) NOT NULL DEFAULT 'pending',
    checked_at    DATETIME,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_records_session FOREIGN KEY (session_id)
        REFERENCES rollcall_sessions (id) ON DELETE CASCADE,
    CONSTRAINT fk_records_student FOREIGN KEY (student_id)
        REFERENCES students (id) ON DELETE RESTRICT,
    CONSTRAINT uk_records_session_student UNIQUE (session_id, student_id),
    CONSTRAINT uk_records_session_order UNIQUE (session_id, order_no),
    CONSTRAINT ck_records_status CHECK (status IN ('pending', 'present', 'absent')),
    CONSTRAINT ck_records_order CHECK (order_no >= 1),
    CONSTRAINT ck_records_checked CHECK (
        (status = 'pending' AND checked_at IS NULL)
        OR (status IN ('present', 'absent') AND checked_at IS NOT NULL)
    ),
    CONSTRAINT ck_records_no_len CHECK (length(student_no) BETWEEN 6 AND 32),
    CONSTRAINT ck_records_name_len CHECK (length(student_name) BETWEEN 1 AND 32),
    CONSTRAINT ck_records_role CHECK (role IN ('学生', '班长', '教师'))
);

CREATE INDEX idx_records_session_status_order
    ON attendance_records (session_id, status, order_no);
CREATE INDEX idx_records_session_order
    ON attendance_records (session_id, order_no);
CREATE INDEX idx_records_student
    ON attendance_records (student_id);

CREATE TABLE users (
    id                    INTEGER NOT NULL PRIMARY KEY,
    username              VARCHAR(32) NOT NULL,
    password_hash         VARCHAR(255) NOT NULL,
    role                  VARCHAR(16) NOT NULL,
    display_name          VARCHAR(32) NOT NULL,
    student_id            INTEGER,
    must_change_password  BOOLEAN NOT NULL DEFAULT 1,
    active                BOOLEAN NOT NULL DEFAULT 1,
    last_login_at         DATETIME,
    token_version         INTEGER NOT NULL DEFAULT 0,
    created_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_users_username UNIQUE (username),
    CONSTRAINT uk_users_student UNIQUE (student_id),
    CONSTRAINT fk_users_student FOREIGN KEY (student_id)
        REFERENCES students (id) ON DELETE RESTRICT,
    CONSTRAINT ck_users_role CHECK (role IN ('teacher', 'monitor', 'student')),
    CONSTRAINT ck_users_binding CHECK (
        (role = 'teacher' AND student_id IS NULL)
        OR (role <> 'teacher' AND student_id IS NOT NULL)
    ),
    CONSTRAINT ck_users_username_len CHECK (length(username) BETWEEN 1 AND 32),
    CONSTRAINT ck_users_display_len CHECK (length(display_name) BETWEEN 1 AND 32),
    CONSTRAINT ck_users_password CHECK (length(password_hash) >= 20),
    CONSTRAINT ck_users_token_version CHECK (token_version >= 0)
);

CREATE INDEX idx_users_role ON users (role);
CREATE INDEX idx_users_active ON users (active);