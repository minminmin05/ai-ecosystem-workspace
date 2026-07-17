import asyncio
from arq import create_pool
from arq.connections import RedisSettings


async def main():
    redis = await create_pool(
        RedisSettings(
            host="localhost",
            port=6379,
            database=0,
        )
    )

    job = await redis.enqueue_job(
        "simple_work",
        {
            "name": "Oat",
            "task": "Test ARQ Worker"
        }
    )

    print("Job ID:", job.job_id)


if __name__ == "__main__":
    asyncio.run(main())