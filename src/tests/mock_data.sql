-- Исходные данные только для тестовой БД.
-- Открытые ключи ниже предназначены только для тестов; в users сохраняются их SHA-256.
-- test_integrator: API-ключ pTcGMT5QVjdo5x3rq9L-OnXLgNhq_fzsDQ52sYR7tpE
-- test_integrator_other: API-ключ LFq9D7yLIWjMQkfYnT1utUYXLHQMjHI3f4yY9rW7RlA
-- test_integrator_many: API-ключ 4eD3BI_AXWNnwHEj4Iy-ZxATMBRX3yX4kpYjKljtyE8
-- test_integrator_inactive: отключён, API-ключ hmNPYy_dCM0Q5058tAPv8hFFoeWowK-MJZ1JWwcNYhs

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
        '3d39c7031760db26018f85d555620efee972fc29bc53d1a20bfd2447c38e2b0c',
        '2026-01-01 00:00:00+00',
        '2026-01-01 00:00:00+00',
        '2026-01-01 00:00:00+00'
    ),
    (
        '019a1000-0000-7000-8000-000000000002',
        'test_integrator_other',
        TRUE,
        '68cc87997ffc8434dc314699ab75a35eb46af91bb9ce2761a11f0bacebc826c4',
        '2026-01-02 00:00:00+00',
        '2026-01-02 00:00:00+00',
        '2026-01-02 00:00:00+00'
    ),
    (
        '019a1000-0000-7000-8000-000000000003',
        'test_integrator_many',
        TRUE,
        '0b547e818a7d8054c7e4a7dd3d2c04f1264d11e373ca3e5c1f989f45cdf13fba',
        '2026-01-03 00:00:00+00',
        '2026-01-03 00:00:00+00',
        '2026-01-03 00:00:00+00'
    ),
    (
        '019a1000-0000-7000-8000-000000000004',
        'test_integrator_inactive',
        FALSE,
        '308e359a1b14972e43f21c7adee85f9efb1acd61e330dc62ec68222f846ac7eb',
        '2026-01-04 00:00:00+00',
        '2026-01-04 00:00:00+00',
        '2026-01-04 00:00:00+00'
    );
