import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

client = AsyncIOMotorClient(Config.MONGO_URI)
db = client[Config.DB_NAME]

users_col = db["users"]
files_col = db["files"]
logs_col = db["admin_logs"]


# ---------------------------------------------------------------- USERS ----
async def add_user(user_id: int, username: str, first_name: str):
    existing = await users_col.find_one({"user_id": user_id})
    if not existing:
        await users_col.insert_one(
            {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "joined_at": datetime.datetime.utcnow(),
                "banned": False,
                "last_seen": datetime.datetime.utcnow(),
            }
        )
        return True  # new user
    else:
        await users_col.update_one(
            {"user_id": user_id},
            {"$set": {"last_seen": datetime.datetime.utcnow(), "username": username}},
        )
        return False


async def is_banned(user_id: int) -> bool:
    u = await users_col.find_one({"user_id": user_id})
    return bool(u and u.get("banned"))


async def ban_user(user_id: int):
    await users_col.update_one({"user_id": user_id}, {"$set": {"banned": True}})


async def unban_user(user_id: int):
    await users_col.update_one({"user_id": user_id}, {"$set": {"banned": False}})


async def total_users() -> int:
    return await users_col.count_documents({})


async def all_user_ids():
    cursor = users_col.find({}, {"user_id": 1})
    return [doc["user_id"] async for doc in cursor]


async def online_users(minutes: int = 10) -> int:
    since = datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)
    return await users_col.count_documents({"last_seen": {"$gte": since}})


# ---------------------------------------------------------------- FILES ----
async def save_file(data: dict):
    await files_col.insert_one(data)


async def get_file(file_code: str):
    return await files_col.find_one({"file_code": file_code})


async def delete_file(file_code: str):
    result = await files_col.delete_one({"file_code": file_code})
    return result.deleted_count > 0


async def rename_file(file_code: str, new_name: str):
    await files_col.update_one({"file_code": file_code}, {"$set": {"file_name": new_name}})


async def toggle_favorite(file_code: str):
    f = await files_col.find_one({"file_code": file_code})
    if not f:
        return None
    new_val = not f.get("favorite", False)
    await files_col.update_one({"file_code": file_code}, {"$set": {"favorite": new_val}})
    return new_val


async def increment_downloads(file_code: str):
    await files_col.update_one({"file_code": file_code}, {"$inc": {"downloads": 1}})


async def user_files(user_id: int, category: str = None, skip: int = 0, limit: int = 10):
    query = {"owner_id": user_id}
    if category:
        query["category"] = category
    cursor = files_col.find(query).sort("uploaded_at", -1).skip(skip).limit(limit)
    return [f async for f in cursor]


async def user_favorites(user_id: int, skip: int = 0, limit: int = 10):
    cursor = (
        files_col.find({"owner_id": user_id, "favorite": True})
        .sort("uploaded_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return [f async for f in cursor]


async def count_user_files(user_id: int, category: str = None) -> int:
    query = {"owner_id": user_id}
    if category:
        query["category"] = category
    return await files_col.count_documents(query)


async def search_user_files(user_id: int, keyword: str, limit: int = 20):
    cursor = files_col.find(
        {"owner_id": user_id, "file_name": {"$regex": keyword, "$options": "i"}}
    ).limit(limit)
    return [f async for f in cursor]


async def search_all_files(keyword: str, limit: int = 20):
    cursor = files_col.find({"file_name": {"$regex": keyword, "$options": "i"}}).limit(limit)
    return [f async for f in cursor]


async def recent_uploads(limit: int = 10):
    cursor = files_col.find().sort("uploaded_at", -1).limit(limit)
    return [f async for f in cursor]


async def total_files() -> int:
    return await files_col.count_documents({})


async def total_storage_bytes() -> int:
    pipeline = [{"$group": {"_id": None, "total": {"$sum": "$file_size"}}}]
    result = await files_col.aggregate(pipeline).to_list(1)
    return result[0]["total"] if result else 0


async def today_uploads() -> int:
    start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return await files_col.count_documents({"uploaded_at": {"$gte": start}})


# ------------------------------------------------------------ ADMIN LOGS ----
async def add_log(admin_id: int, action: str):
    await logs_col.insert_one(
        {"admin_id": admin_id, "action": action, "time": datetime.datetime.utcnow()}
    )


async def get_logs(limit: int = 20):
    cursor = logs_col.find().sort("time", -1).limit(limit)
    return [l async for l in cursor]
