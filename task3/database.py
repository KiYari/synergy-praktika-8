import asyncpg
import asyncio

async def init_db():
    conn = await asyncpg.connect(
        user="your_username",
        password="your_password",
        database="your_database",
        host="localhost"
    )

    await conn.execute('''
        CREATE TABLE IF NOT EXISTS problems (
            issue_id VARCHAR(50) PRIMARY KEY,
            user_description TEXT NOT NULL,
            category VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'new'
        )
    ''')

    await conn.execute('''
        CREATE TABLE IF NOT EXISTS symptoms (
            symptom_id SERIAL PRIMARY KEY,
            issue_id VARCHAR(50) NOT NULL REFERENCES problems(issue_id) ON DELETE CASCADE,
            type VARCHAR(50) NOT NULL,
            value TEXT NOT NULL,
            environment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    await conn.close()

if __name__ == "__main__":
    asyncio.run(init_db())