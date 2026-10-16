import aiosqlite
from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                client_type TEXT DEFAULT 'individual',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS base_prices (
                network TEXT,
                fuel_type TEXT,
                base_price_uah REAL,
                PRIMARY KEY (network, fuel_type)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                network TEXT,
                fuel_type TEXT,
                liters INTEGER,
                payment_method TEXT,
                total_uah REAL,
                total_usdt REAL,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS coupons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                network TEXT,
                fuel_type TEXT,
                liters INTEGER,
                status TEXT DEFAULT 'available',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Seed default prices if empty
        async with db.execute("SELECT COUNT(*) FROM base_prices") as cursor:
            count = (await cursor.fetchone())[0]
            if count == 0:
                default_prices = [
                    ('wog', 'a95', 58.50),
                    ('wog', 'dp', 55.00),
                    ('wog', 'gas', 29.50),
                    ('okko', 'a95', 58.50),
                    ('okko', 'dp', 55.00),
                    ('okko', 'gas', 29.50),
                    ('ukrnafta', 'a95', 54.00),
                    ('ukrnafta', 'dp', 51.00),
                    ('ukrnafta', 'gas', 27.50),
                ]
                await db.executemany(
                    "INSERT INTO base_prices (network, fuel_type, base_price_uah) VALUES (?, ?, ?)",
                    default_prices
                )
        await db.commit()

async def get_price(network: str, fuel_type: str) -> float:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT base_price_uah FROM base_prices WHERE network = ? AND fuel_type = ?",
            (network, fuel_type)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 55.0

async def add_or_update_user(telegram_id: int, username: str, full_name: str, phone: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (telegram_id, username, full_name, phone)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username=excluded.username,
                full_name=excluded.full_name,
                phone=CASE WHEN excluded.phone != '' THEN excluded.phone ELSE users.phone END
        """, (telegram_id, username, full_name, phone))
        await db.commit()

async def create_order(telegram_id: int, network: str, fuel_type: str, liters: int, payment_method: str, total_uah: float, total_usdt: float) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO orders (telegram_id, network, fuel_type, liters, payment_method, total_uah, total_usdt, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending_payment')
        """, (telegram_id, network, fuel_type, liters, payment_method, total_uah, total_usdt))
        await db.commit()
        return cursor.lastrowid

async def get_user_coupons(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM coupons WHERE telegram_id = ? AND status = 'available' ORDER BY id DESC",
            (telegram_id,)
        ) as cursor:
            return await cursor.fetchall()

async def add_demo_coupons(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM coupons WHERE telegram_id = ?", (telegram_id,)) as cursor:
            if (await cursor.fetchone())[0] == 0:
                demo_data = [
                    (telegram_id, 'wog', 'a95', 20, 'available'),
                    (telegram_id, 'okko', 'dp', 30, 'available'),
                    (telegram_id, 'ukrnafta', 'gas', 10, 'available'),
                ]
                await db.executemany(
                    "INSERT INTO coupons (telegram_id, network, fuel_type, liters, status) VALUES (?, ?, ?, ?, ?)",
                    demo_data
                )
                await db.commit()
