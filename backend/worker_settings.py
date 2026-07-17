from arq.connections import RedisSettings


async def simple_work(ctx, job_data):
    print("=== Job Received ===")
    print(f"Job Data: {job_data}")


class WorkerSettings:
    functions = [
        simple_work,
    ]

    redis_settings = RedisSettings(
        host="localhost",
        port=6379,
        database=0,
    )