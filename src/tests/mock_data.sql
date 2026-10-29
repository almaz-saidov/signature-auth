-- Исходные пользователи для тестов БД; значения хешей условные.
INSERT INTO users (
    id,
    username,
    is_active,
    api_key_hash,
    api_key_created_at,
    created_at,
    updated_at
)
VALUES
    (
        '019a1000-0000-7000-8000-000000000001',
        'test_integrator',
        TRUE,
        'test-api-key-hash-1',
        '2026-01-01 00:00:00+00',
        '2026-01-01 00:00:00+00',
        '2026-01-01 00:00:00+00'
    ),
    (
        '019a1000-0000-7000-8000-000000000002',
        'test_integrator_other',
        TRUE,
        'test-api-key-hash-2',
        '2026-01-01 00:00:00+00',
        '2026-01-01 00:00:00+00',
        '2026-01-01 00:00:00+00'
    );
