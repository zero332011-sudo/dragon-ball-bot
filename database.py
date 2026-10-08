import aiosqlite

DB_NAME = "database.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                file_id TEXT NOT NULL
            )
        """)
        await db.commit()

async def add_episode(title: str, file_id: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO episodes (title, file_id) VALUES (?, ?)", (title, file_id))
        await db.commit()

async def get_all_episodes():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id, title, file_id FROM episodes") as cursor:
            return await cursor.fetchall()

async def delete_episode(episode_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM episodes WHERE id = ?", (episode_id,))
        await db.commit()
        
