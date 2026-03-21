import asyncio
import uuid
from orchestrator import chat_xray, XRayRequest
from auth import AuthUser

async def run_test():
    try:
        req = XRayRequest(
            user_id="test_user_from_post",
            session_id=str(uuid.uuid4()),
            message=""
        )
        auth = AuthUser(user_id="test_user_from_post")
        
        print("Calling orchestrator.chat_xray()...")
        res = await chat_xray(req, auth)
        print("Success! Response:", res)
    except Exception as e:
        import traceback
        print("--- CRASH REPRODUCED ---")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
