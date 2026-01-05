from fastapi import Header, HTTPException, status

def get_user_id(x_user_id: str = Header(...)) -> str:
    """Extract User Id from Header"""
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid User Id")
    return x_user_id