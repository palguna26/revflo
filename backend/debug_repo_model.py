from app.models.repo import Repo
from beanie import PydanticObjectId
import json

def test_serialization():
    # Create a dummy repo
    r = Repo(
        id=PydanticObjectId(),
        repo_full_name="test/repo",
        owner="test",
        name="repo"
    )
    # Serialize using Pydantic v2 dump (or v1 dict/json depending on environment)
    # Beanie uses Pydantic.
    try:
        # FastAPI uses .model_dump() usually in Pydantic v2
        data = r.model_dump()
        print("Keys in model_dump:", data.keys())
        # Check if id is there
        if 'id' in data:
            print("ID is present in dump.")
        else:
            print("ID is MISSING in dump.")
            
        json_out = r.model_dump_json()
        print("JSON output:", json_out)
        
    except AttributeError:
        # Pydantic v1
        data = r.dict()
        print("Keys in dict:", data.keys())
        if 'id' in data:
            print("ID is present in dump.")
        else:
            print("ID is MISSING in dump.")

if __name__ == "__main__":
    test_serialization()
