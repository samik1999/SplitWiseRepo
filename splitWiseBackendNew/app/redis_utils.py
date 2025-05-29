import redis.asyncio as redis 
import json 
from typing import Optional, Any 
from app.config import settings 

redis_connection_pool = None 

async def initialize_redis_connection_pool():
    global redis_connection_pool
    
    if redis_connection_pool is None and settings.REDIS_HOST:
        try:
            # Create the connection pool object
            redis_connection_pool = redis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB, 
                password=settings.REDIS_PASSWORD, 
                decode_responses=False 
            )
            # Try to connect and ping Redis to ensure it's working
            test_redis_client = redis.Redis(connection_pool=redis_connection_pool)
            await test_redis_client.ping() 
            await test_redis_client.close() 
            print(f"Successfully connected to Redis and initialized pool: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            print(f"ERROR: Failed to initialize Redis connection pool or ping Redis: {e}")
            redis_connection_pool = None 

async def get_redis_client_from_pool():

    if redis_connection_pool is None:
        return None
    return redis.Redis(connection_pool=redis_connection_pool)

async def close_down_redis_connection_pool():
    global redis_connection_pool
    if redis_connection_pool:
        
        print("Redis connection pool resources are being released (if applicable).")
        redis_connection_pool = None


# --- Basic Caching Helper Functions ---

async def store_value_in_cache(cache_key: str, value_to_store: Any, expiration_time_seconds: Optional[int] = None) -> bool:
    
    redis_client = await get_redis_client_from_pool()
    if not redis_client:
       
        return False 

    try:
        json_string_value = json.dumps(value_to_store)
        
       
        if expiration_time_seconds is None:
            expiration_time_seconds = settings.CACHE_EXPIRATION_SECONDS
            
        # Store the JSON string in Redis (as bytes) with the specified expiration time
        await redis_client.set(name=cache_key, value=json_string_value.encode('utf-8'), ex=expiration_time_seconds)
       
        return True
    except Exception as e:
        print(f"ERROR: Failed to store value in cache for key '{cache_key}': {e}")
        return False
    finally:
        if redis_client:
            await redis_client.close() 

async def retrieve_value_from_cache(cache_key: str) -> Optional[Any]:
    redis_client = await get_redis_client_from_pool()
    if not redis_client:
        return None

    try:
        cached_value_as_bytes = await redis_client.get(cache_key)
        
        if cached_value_as_bytes:
            json_string = cached_value_as_bytes.decode('utf-8')
            python_object = json.loads(json_string)
            
            return python_object
        else:
            
            return None 
    except Exception as e:
        print(f"ERROR: Failed to retrieve or deserialize value from cache for key '{cache_key}': {e}")
        return None
    finally:
        if redis_client:
            await redis_client.close()

async def remove_value_from_cache(cache_key: str) -> bool:
    
    redis_client = await get_redis_client_from_pool()
    if not redis_client:
        return False

    try:
        
        number_of_keys_deleted = await redis_client.delete(cache_key)
        if number_of_keys_deleted > 0:
           
            return True
        else:
           
            return False
    except Exception as e:
        print(f"ERROR: Failed to delete value from cache for key '{cache_key}': {e}")
        return False
    finally:
        if redis_client:
            await redis_client.close()


def generate_cache_key_for_user_details(user_id: int) -> str:
    return f"user_info:{user_id}" 

def generate_cache_key_for_user_id_by_email(email: str) -> str:
   
    return f"user_id_lookup_email:{email.lower()}"


def generate_cache_key_for_user_balance_summary(user_id: int) -> str:
    return f"user_balance_summary:{user_id}"


def generate_cache_key_for_expense_splits_list(expense_id: int) -> str:
    return f"expense:{expense_id}:splits_list"