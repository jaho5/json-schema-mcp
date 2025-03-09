from mcp.server.fastmcp import FastMCP
import os
import json
import uuid
from pathlib import Path

# Create the MCP server
mcp = FastMCP("JSON Schema Server")

# Set up schemas directory
SCHEMAS_DIR = Path("schemas")
os.makedirs(SCHEMAS_DIR, exist_ok=True)

# Schema management functions
def get_schema_path(schema_id):
    """Get the file path for a schema by ID"""
    return SCHEMAS_DIR / f"{schema_id}.json"

def list_schemas():
    """Get list of available schemas"""
    schemas = []
    for file in SCHEMAS_DIR.glob("*.json"):
        schema_id = file.stem
        try:
            with open(file, "r") as f:
                schema = json.load(f)
                name = schema.get("title", schema_id)
                schemas.append({"id": schema_id, "name": name})
        except Exception as e:
            print(f"Error reading schema {file}: {e}")
    return schemas

def save_schema(schema):
    """Save schema to file, assign ID if needed"""
    if schema.get("$id") is None:
        schema["$id"] = str(uuid.uuid4())
    
    schema_id = schema["$id"]
    schema_path = get_schema_path(schema_id)
    
    with open(schema_path, "w") as f:
        json.dump(schema, f, indent=2)
    
    return schema_id

# Resource: Get a specific schema
@mcp.resource("schema://{schema_id}")
def get_schema(schema_id: str) -> str:
    """Get a JSON schema by ID"""
    schema_path = get_schema_path(schema_id)
    
    if not schema_path.exists():
        return f"Schema with ID '{schema_id}' not found"
    
    with open(schema_path, "r") as f:
        return f.read()

# Resource: List all schemas
@mcp.resource("schemas://list")
def get_schemas_list() -> str:
    """List all available JSON schemas"""
    schemas = list_schemas()
    return json.dumps(schemas, indent=2)

# Tool: Create a new JSON schema
@mcp.tool()
def create_schema(title: str, type: str = "object", properties: dict = None, required: list = None) -> str:
    """
    Create a new JSON schema
    
    Args:
        title: The title of the schema
        type: The type of the schema (object, array, string, number, etc.)
        properties: Dictionary of property definitions
        required: List of required property names
    """
    schema = {
        "title": title,
        "type": type
    }
    
    if properties:
        schema["properties"] = properties
    
    if required:
        schema["required"] = required
    
    schema_id = save_schema(schema)
    return f"Schema created with ID: {schema_id}"

# Tool: Create an instance from a schema
@mcp.tool()
def create_instance(schema_id: str, values: dict = None) -> str:
    """
    Create a JSON instance based on a schema
    
    Args:
        schema_id: ID of the schema to use
        values: Values to populate in the instance
    """
    schema_path = get_schema_path(schema_id)
    
    if not schema_path.exists():
        return f"Schema with ID '{schema_id}' not found"
    
    with open(schema_path, "r") as f:
        schema = json.load(f)
    
    # Create a simple instance based on schema
    instance = {}
    
    if schema.get("type") == "object" and schema.get("properties"):
        for prop_name, prop_def in schema["properties"].items():
            # Use provided value or a default based on type
            if values and prop_name in values:
                instance[prop_name] = values[prop_name]
            else:
                # Simple default values based on property type
                prop_type = prop_def.get("type", "string")
                if prop_type == "string":
                    instance[prop_name] = ""
                elif prop_type == "number" or prop_type == "integer":
                    instance[prop_name] = 0
                elif prop_type == "boolean":
                    instance[prop_name] = False
                elif prop_type == "array":
                    instance[prop_name] = []
                elif prop_type == "object":
                    instance[prop_name] = {}
                # Add other type defaults as needed
    
    return json.dumps(instance, indent=2)

# Run the server
if __name__ == "__main__":
    mcp.run(transport="stdio")
