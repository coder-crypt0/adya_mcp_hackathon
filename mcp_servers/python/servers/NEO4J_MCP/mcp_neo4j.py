import logging
from collections.abc import Sequence
from typing import Any, Dict, List, Optional, Union
import json
import traceback
from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
import mcp.server.stdio
import mcp.types as types

# Neo4j imports
try:
    from neo4j import GraphDatabase, exceptions as neo4j_exceptions
    from neo4j.exceptions import ServiceUnavailable, AuthError, CypherSyntaxError
except ImportError:
    GraphDatabase = None
    neo4j_exceptions = None
    ServiceUnavailable = Exception
    AuthError = Exception
    CypherSyntaxError = Exception

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neo4j-mcp")

# MCP server instance
app = Server("neo4j-mcp")

class Neo4jConnection:
    """Neo4j database connection manager"""
    
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        if GraphDatabase is None:
            raise ImportError("neo4j package not installed. Run: pip install neo4j")
        
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self._driver = None
    
    def connect(self):
        """Establish connection to Neo4j"""
        try:
            self._driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            # Test connection
            with self._driver.session(database=self.database) as session:
                session.run("RETURN 1")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            return False
    
    def close(self):
        """Close connection"""
        if self._driver:
            self._driver.close()
    
    def execute_query(self, query: str, parameters: dict = None):
        """Execute a Cypher query"""
        if not self._driver:
            raise Exception("Not connected to Neo4j")
        
        try:
            with self._driver.session(database=self.database) as session:
                result = session.run(query, parameters or {})
                records = []
                for record in result:
                    record_dict = {}
                    for key in record.keys():
                        value = record[key]
                        # Convert Neo4j types to serializable formats
                        record_dict[key] = self._serialize_neo4j_value(value)
                    records.append(record_dict)
                
                return {
                    "records": records,
                    "summary": {
                        "query": query,
                        "parameters": parameters,
                        "counters": result.consume().counters.__dict__ if hasattr(result, 'consume') else {}
                    }
                }
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def _serialize_neo4j_value(self, value):
        """Convert Neo4j types to JSON-serializable formats"""
        # Handle None
        if value is None:
            return None
        
        # Handle Node and Relationship objects
        if hasattr(value, '_properties'):
            serialized = {}
            # Convert properties recursively
            for prop_key, prop_value in value._properties.items():
                serialized[prop_key] = self._serialize_neo4j_value(prop_value)
            
            # Add metadata
            if hasattr(value, 'labels'):  # Node
                serialized['_type'] = list(value.labels)
            elif hasattr(value, 'type'):  # Relationship
                serialized['_type'] = str(value.type)
            
            # Use element_id if available (newer Neo4j versions), fallback to id
            if hasattr(value, 'element_id'):
                serialized['_id'] = value.element_id
            elif hasattr(value, 'id'):
                serialized['_id'] = value.id
            
            return serialized
        
        # Handle DateTime objects
        if hasattr(value, 'iso_format'):  # Neo4j DateTime
            return value.iso_format()
        
        # Handle Date objects
        if hasattr(value, 'year') and hasattr(value, 'month') and hasattr(value, 'day'):
            if hasattr(value, 'hour'):  # DateTime-like
                return value.isoformat() if hasattr(value, 'isoformat') else str(value)
            else:  # Date-like
                return value.isoformat() if hasattr(value, 'isoformat') else str(value)
        
        # Handle Time objects
        if hasattr(value, 'hour') and hasattr(value, 'minute') and hasattr(value, 'second'):
            return value.isoformat() if hasattr(value, 'isoformat') else str(value)
        
        # Handle Duration objects
        if hasattr(value, 'months') and hasattr(value, 'days') and hasattr(value, 'seconds'):
            return str(value)
        
        # Handle Point objects (spatial data)
        if hasattr(value, 'srid') and hasattr(value, 'x') and hasattr(value, 'y'):
            result = {'srid': value.srid, 'x': value.x, 'y': value.y}
            if hasattr(value, 'z'):
                result['z'] = value.z
            return result
        
        # Handle lists recursively
        if isinstance(value, list):
            return [self._serialize_neo4j_value(item) for item in value]
        
        # Handle dictionaries recursively
        if isinstance(value, dict):
            return {k: self._serialize_neo4j_value(v) for k, v in value.items()}
        
        # Handle basic types (str, int, float, bool)
        if isinstance(value, (str, int, float, bool)):
            return value
        
        # Fallback: convert to string
        return str(value)

# Tool handler base class
class Neo4jToolHandler:
    def __init__(self, name: str):
        self.name = name

    def get_tool_description(self) -> Tool:
        raise NotImplementedError()

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        raise NotImplementedError()

    def get_connection(self, credentials: dict) -> Neo4jConnection:
        """Get Neo4j connection from credentials"""
        if not credentials:
            raise ValueError("Neo4j credentials are required")
        
        uri = credentials.get("uri", "bolt://localhost:7687")
        username = credentials.get("username", "neo4j")
        password = credentials.get("password", "")
        database = credentials.get("database", "neo4j")
        
        if not password:
            raise ValueError("Neo4j password is required")
        
        conn = Neo4jConnection(uri, username, password, database)
        if not conn.connect():
            raise Exception("Failed to connect to Neo4j database")
        
        return conn

# 1. Database Management Tools
class DatabaseInfoToolHandler(Neo4jToolHandler):
    def __init__(self):
        super().__init__("get_database_info")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Get Neo4j database information including version, edition, and statistics",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            conn = self.get_connection(credentials)
            
            # Get database info
            queries = [
                ("CALL dbms.components() YIELD name, versions, edition", "Database components"),
                ("MATCH (n) RETURN count(n) as nodeCount", "Node count"),
                ("MATCH ()-[r]->() RETURN count(r) as relCount", "Relationship count"),
                ("CALL db.labels() YIELD label RETURN count(label) as labelCount", "Label count"),
                ("CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) as typeCount", "Relationship type count")
            ]
            
            results = {}
            for query, description in queries:
                try:
                    result = conn.execute_query(query)
                    results[description] = result
                except Exception as e:
                    results[description] = f"Error: {str(e)}"
            
            conn.close()
            return [TextContent(type="text", text=f"Database Information:\n{json.dumps(results, indent=2)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting database info: {str(e)}")]

class ListConstraintsToolHandler(Neo4jToolHandler):
    def __init__(self):
        super().__init__("list_constraints")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="List all constraints in the database",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            conn = self.get_connection(credentials)
            
            result = conn.execute_query("SHOW CONSTRAINTS")
            conn.close()
            
            return [TextContent(type="text", text=f"Constraints:\n{json.dumps(result, indent=2)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error listing constraints: {str(e)}")]

class ListIndexesToolHandler(Neo4jToolHandler):
    def __init__(self):
        super().__init__("list_indexes")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="List all indexes in the database",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            conn = self.get_connection(credentials)
            
            result = conn.execute_query("SHOW INDEXES")
            conn.close()
            
            return [TextContent(type="text", text=f"Indexes:\n{json.dumps(result, indent=2)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error listing indexes: {str(e)}")]

class ListLabelsToolHandler(Neo4jToolHandler):
    def __init__(self):
        super().__init__("list_labels")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="List all node labels in the database with their counts",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            conn = self.get_connection(credentials)
            
            # Get all labels and their counts
            result = conn.execute_query("CALL db.labels() YIELD label RETURN label")
            labels_info = []
            
            if result and result.get("records"):
                for record in result["records"]:
                    label = record["label"]
                    # Get count for each label
                    count_result = conn.execute_query(f"MATCH (n:`{label}`) RETURN count(n) as nodeCount")
                    count = count_result["records"][0]["nodeCount"] if count_result["records"] else 0
                    labels_info.append({"label": label, "count": count})
            
            conn.close()
            
            return [TextContent(type="text", text=f"Database Labels:\n{json.dumps(labels_info, indent=2)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error listing labels: {str(e)}")]

# 2. Node Operations
class CreateNodeToolHandler(Neo4jToolHandler):
    def __init__(self):
        super().__init__("create_node")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Create a new node with specified labels and properties",
            inputSchema={
                "type": "object",
                "properties": {
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of labels for the node"
                    },
                    "properties": {
                        "type": "object",
                        "description": "Properties for the node as key-value pairs"
                    }
                },
                "required": ["labels", "properties"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            conn = self.get_connection(credentials)
            
            labels = args["labels"]
            properties = args["properties"]
            
            # Build labels string
            labels_str = ":".join(labels)
            
            # Create node
            query = f"CREATE (n:{labels_str} $props) RETURN n"
            result = conn.execute_query(query, {"props": properties})
            conn.close()
            
            return [TextContent(type="text", text=f"Node created:\n{json.dumps(result, indent=2)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error creating node: {str(e)}")]

class FindNodesToolHandler(Neo4jToolHandler):
    def __init__(self):
        super().__init__("find_nodes")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Find nodes by label and/or properties",
            inputSchema={
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "description": "Label to search for (optional)"
                    },
                    "properties": {
                        "type": "object",
                        "description": "Properties to match (optional)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of nodes to return",
                        "default": 100
                    }
                }
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            conn = self.get_connection(credentials)
            
            label = args.get("label")
            properties = args.get("properties", {})
            limit = args.get("limit", 100)
            
            # Build query with case-insensitive label matching
            if label:
                # Try different case variations to find existing nodes
                label_variations = [
                    label.capitalize(),  # First letter uppercase (most common)
                    label,  # Original case
                    label.upper(),  # All uppercase
                    label.lower()   # All lowercase
                ]
                
                successful_label = None
                
                # Test each label variation to see which one has nodes
                for label_variant in label_variations:
                    try:
                        # Remove any special characters that might cause issues
                        clean_label = ''.join(c for c in label_variant if c.isalnum() or c in ['_'])
                        
                        test_query = f"MATCH (n:`{clean_label}`) RETURN count(n) as nodeCount"
                        test_result = conn.execute_query(test_query)
                        
                        if test_result and test_result.get("records") and len(test_result["records"]) > 0:
                            node_count = test_result["records"][0].get("nodeCount", 0)
                            if node_count > 0:
                                successful_label = clean_label
                                break
                    except Exception as e:
                        # Log the error but continue trying other variations
                        logger.debug(f"Label variation '{label_variant}' failed: {str(e)}")
                        continue
                
                # Use the successful label or fall back to original
                if successful_label:
                    query = f"MATCH (n:`{successful_label}`)"
                else:
                    # If no variation works, try the original with backticks for safety
                    clean_original = ''.join(c for c in label if c.isalnum() or c in ['_'])
                    query = f"MATCH (n:`{clean_original}`)"
            else:
                query = "MATCH (n)"
            
            if properties:
                conditions = []
                params = {}
                for key, value in properties.items():
                    param_name = f"prop_{key}"
                    conditions.append(f"n.{key} = ${param_name}")
                    params[param_name] = value
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            else:
                params = {}
            
            query += f" RETURN n LIMIT {limit}"
            
            result = conn.execute_query(query, params)
            conn.close()
            
            return [TextContent(type="text", text=f"Found nodes:\n{json.dumps(result, indent=2)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error finding nodes: {str(e)}")]

class UpdateNodeToolHandler(Neo4jToolHandler):
    def __init__(self):
        super().__init__("update_node")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Update node properties by node ID or matching criteria",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "integer",
                        "description": "ID of the node to update (optional)"
                    },
                    "match_properties": {
                        "type": "object",
                        "description": "Properties to match for finding nodes to update (optional)"
                    },
                    "label": {
                        "type": "string",
                        "description": "Label to match (optional)"
                    },
                    "update_properties": {
                        "type": "object",
                        "description": "Properties to update"
                    }
                },
                "required": ["update_properties"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            conn = self.get_connection(credentials)
            
            node_id = args.get("node_id")
            match_properties = args.get("match_properties", {})
            label = args.get("label")
            update_properties = args["update_properties"]
            
            # Build query
            if node_id:
                query = f"MATCH (n) WHERE ID(n) = {node_id}"
            else:
                if label:
                    query = f"MATCH (n:{label})"
                else:
                    query = "MATCH (n)"
                
                if match_properties:
                    conditions = []
                    params = {}
                    for key, value in match_properties.items():
                        param_name = f"match_{key}"
                        conditions.append(f"n.{key} = ${param_name}")
                        params[param_name] = value
                    
                    if conditions:
                        query += " WHERE " + " AND ".join(conditions)
                else:
                    params = {}
            
            # Add update clause
            update_clauses = []
            for key, value in update_properties.items():
                param_name = f"update_{key}"
                update_clauses.append(f"n.{key} = ${param_name}")
                params[param_name] = value
            
            query += " SET " + ", ".join(update_clauses) + " RETURN n"
            
            result = conn.execute_query(query, params)
            conn.close()
            
            return [TextContent(type="text", text=f"Updated nodes:\n{json.dumps(result, indent=2)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error updating node: {str(e)}")]

class DeleteNodeToolHandler(Neo4jToolHandler):
    def __init__(self):
        super().__init__("delete_node")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Delete nodes by ID or matching criteria",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "integer",
                        "description": "ID of the node to delete (optional)"
                    },
                    "match_properties": {
                        "type": "object",
                        "description": "Properties to match for finding nodes to delete (optional)"
                    },
                    "label": {
                        "type": "string",
                        "description": "Label to match (optional)"
                    },
                    "detach": {
                        "type": "boolean",
                        "description": "Whether to detach (delete relationships) before deleting node",
                        "default": True
                    }
                }
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            conn = self.get_connection(credentials)
            
            node_id = args.get("node_id")
            match_properties = args.get("match_properties", {})
            label = args.get("label")
            detach = args.get("detach", True)
            
            # Build query
            if node_id:
                query = f"MATCH (n) WHERE ID(n) = {node_id}"
                params = {}
            else:
                if label:
                    query = f"MATCH (n:{label})"
                else:
                    query = "MATCH (n)"
                
                params = {}
                if match_properties:
                    conditions = []
                    for key, value in match_properties.items():
                        param_name = f"match_{key}"
                        conditions.append(f"n.{key} = ${param_name}")
                        params[param_name] = value
                    
                    if conditions:
                        query += " WHERE " + " AND ".join(conditions)
            
            # Add delete clause
            if detach:
                query += " DETACH DELETE n"
            else:
                query += " DELETE n"
            
            result = conn.execute_query(query, params)
            conn.close()
            
            return [TextContent(type="text", text=f"Delete operation completed:\n{json.dumps(result, indent=2)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error deleting node: {str(e)}")]

# 3. Relationship Operations
class CreateRelationshipToolHandler(Neo4jToolHandler):
    def __init__(self):
        super().__init__("create_relationship")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Create a relationship between two nodes",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_node_id": {
                        "type": "integer",
                        "description": "ID of the source node (optional)"
                    },
                    "to_node_id": {
                        "type": "integer",
                        "description": "ID of the target node (optional)"
                    },
                    "from_node_match": {
                        "type": "object",
                        "description": "Properties to match source node (optional)"
                    },
                    "to_node_match": {
                        "type": "object",
                        "description": "Properties to match target node (optional)"
                    },
                    "from_label": {
                        "type": "string",
                        "description": "Label of source node (optional)"
                    },
                    "to_label": {
                        "type": "string",
                        "description": "Label of target node (optional)"
                    },
                    "relationship_type": {
                        "type": "string",
                        "description": "Type of the relationship"
                    },
                    "properties": {
                        "type": "object",
                        "description": "Properties for the relationship"
                    }
                },
                "required": ["relationship_type"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            conn = self.get_connection(credentials)
            
            from_node_id = args.get("from_node_id")
            to_node_id = args.get("to_node_id")
            from_node_match = args.get("from_node_match", {})
            to_node_match = args.get("to_node_match", {})
            from_label = args.get("from_label")
            to_label = args.get("to_label")
            relationship_type = args["relationship_type"]
            properties = args.get("properties", {})
            
            params = {}
            
            # Build query conditions
            where_conditions = []
            
            # Build from node match
            if from_node_id:
                query = f"MATCH (a) WHERE ID(a) = {from_node_id}"
            else:
                if from_label:
                    query = f"MATCH (a:{from_label})"
                else:
                    query = "MATCH (a)"
                
                if from_node_match:
                    for key, value in from_node_match.items():
                        param_name = f"from_{key}"
                        where_conditions.append(f"a.{key} = ${param_name}")
                        params[param_name] = value
            
            # Build to node match
            if to_node_id:
                query += f" MATCH (b) WHERE ID(b) = {to_node_id}"
            else:
                if to_label:
                    query += f" MATCH (b:{to_label})"
                else:
                    query += " MATCH (b)"
                
                if to_node_match:
                    for key, value in to_node_match.items():
                        param_name = f"to_{key}"
                        where_conditions.append(f"b.{key} = ${param_name}")
                        params[param_name] = value
            
            # Add WHERE clause if needed
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
            
            # Build relationship creation
            if properties:
                params["rel_props"] = properties
                query += f" CREATE (a)-[r:{relationship_type} $rel_props]->(b) RETURN r"
            else:
                query += f" CREATE (a)-[r:{relationship_type}]->(b) RETURN r"
            
            result = conn.execute_query(query, params)
            conn.close()
            
            return [TextContent(type="text", text=f"Relationship created:\n{json.dumps(result, indent=2)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error creating relationship: {str(e)}")]

class FindRelationshipsToolHandler(Neo4jToolHandler):
    def __init__(self):
        super().__init__("find_relationships")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Find relationships by type and/or properties",
            inputSchema={
                "type": "object",
                "properties": {
                    "relationship_type": {
                        "type": "string",
                        "description": "Type of relationship to find (optional)"
                    },
                    "properties": {
                        "type": "object",
                        "description": "Properties to match (optional)"
                    },
                    "from_label": {
                        "type": "string",
                        "description": "Label of source nodes (optional)"
                    },
                    "to_label": {
                        "type": "string",
                        "description": "Label of target nodes (optional)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of relationships to return",
                        "default": 100
                    }
                }
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            conn = self.get_connection(credentials)
            
            relationship_type = args.get("relationship_type")
            properties = args.get("properties", {})
            from_label = args.get("from_label")
            to_label = args.get("to_label")
            limit = args.get("limit", 100)
            
            # Build query
            from_part = f"(a:{from_label})" if from_label else "(a)"
            to_part = f"(b:{to_label})" if to_label else "(b)"
            
            if relationship_type:
                rel_part = f"[r:{relationship_type}]"
            else:
                rel_part = "[r]"
            
            query = f"MATCH {from_part}-{rel_part}->{to_part}"
            
            params = {}
            if properties:
                conditions = []
                for key, value in properties.items():
                    param_name = f"prop_{key}"
                    conditions.append(f"r.{key} = ${param_name}")
                    params[param_name] = value
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            query += f" RETURN a, r, b LIMIT {limit}"
            
            result = conn.execute_query(query, params)
            conn.close()
            
            return [TextContent(type="text", text=f"Found relationships:\n{json.dumps(result, indent=2)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error finding relationships: {str(e)}")]

# 4. Graph Analysis Tools
class ShortestPathToolHandler(Neo4jToolHandler):
    def __init__(self):
        super().__init__("shortest_path")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Find shortest path between two nodes",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_node_id": {
                        "type": "integer",
                        "description": "ID of the source node (optional)"
                    },
                    "to_node_id": {
                        "type": "integer",
                        "description": "ID of the target node (optional)"
                    },
                    "from_node_match": {
                        "type": "object",
                        "description": "Properties to match source node (optional)"
                    },
                    "to_node_match": {
                        "type": "object",
                        "description": "Properties to match target node (optional)"
                    },
                    "from_label": {
                        "type": "string",
                        "description": "Label of source node (optional)"
                    },
                    "to_label": {
                        "type": "string",
                        "description": "Label of target node (optional)"
                    },
                    "relationship_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Allowed relationship types (optional)"
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum path depth",
                        "default": 15
                    }
                }
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            conn = self.get_connection(credentials)
            
            from_node_id = args.get("from_node_id")
            to_node_id = args.get("to_node_id")
            from_node_match = args.get("from_node_match", {})
            to_node_match = args.get("to_node_match", {})
            from_label = args.get("from_label")
            to_label = args.get("to_label")
            relationship_types = args.get("relationship_types", [])
            max_depth = args.get("max_depth", 15)
            
            params = {}
            
            # Build WHERE conditions
            where_conditions = []
            
            # Build from node match
            if from_node_id:
                query = f"MATCH (start) WHERE ID(start) = {from_node_id}"
            else:
                if from_label:
                    query = f"MATCH (start:{from_label})"
                else:
                    query = "MATCH (start)"
                
                if from_node_match:
                    for key, value in from_node_match.items():
                        param_name = f"from_{key}"
                        where_conditions.append(f"start.{key} = ${param_name}")
                        params[param_name] = value
            
            # Build to node match
            if to_node_id:
                query += f" MATCH (end) WHERE ID(end) = {to_node_id}"
            else:
                if to_label:
                    query += f" MATCH (end:{to_label})"
                else:
                    query += " MATCH (end)"
                
                if to_node_match:
                    for key, value in to_node_match.items():
                        param_name = f"to_{key}"
                        where_conditions.append(f"end.{key} = ${param_name}")
                        params[param_name] = value
            
            # Add WHERE clause if needed
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
            
            # Build relationship pattern
            if relationship_types:
                rel_pattern = "|".join(relationship_types)
                rel_part = f"[:{rel_pattern}*1..{max_depth}]"
            else:
                rel_part = f"[*1..{max_depth}]"
            
            query += f" WITH start, end MATCH path = shortestPath((start)-{rel_part}-(end)) RETURN path"
            
            result = conn.execute_query(query, params)
            conn.close()
            
            return [TextContent(type="text", text=f"Shortest path:\n{json.dumps(result, indent=2)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error finding shortest path: {str(e)}")]

class GetNeighborsToolHandler(Neo4jToolHandler):
    def __init__(self):
        super().__init__("get_neighbors")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Get neighboring nodes of a given node",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "integer",
                        "description": "ID of the node (optional)"
                    },
                    "node_match": {
                        "type": "object",
                        "description": "Properties to match the node (optional)"
                    },
                    "label": {
                        "type": "string",
                        "description": "Label of the node (optional)"
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["incoming", "outgoing", "both"],
                        "description": "Direction of relationships",
                        "default": "both"
                    },
                    "relationship_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by relationship types (optional)"
                    },
                    "depth": {
                        "type": "integer",
                        "description": "Depth of neighbors to fetch",
                        "default": 1
                    }
                }
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            conn = self.get_connection(credentials)
            
            node_id = args.get("node_id")
            node_match = args.get("node_match", {})
            label = args.get("label")
            direction = args.get("direction", "both")
            relationship_types = args.get("relationship_types", [])
            depth = args.get("depth", 1)
            
            params = {}
            
            # Build query
            if node_id:
                query = f"MATCH (n) WHERE ID(n) = {node_id}"
                where_conditions = []
            else:
                if label:
                    query = f"MATCH (n:{label})"
                else:
                    query = "MATCH (n)"
                
                where_conditions = []
                if node_match:
                    for key, value in node_match.items():
                        param_name = f"node_{key}"
                        where_conditions.append(f"n.{key} = ${param_name}")
                        params[param_name] = value
                
                if where_conditions:
                    query += " WHERE " + " AND ".join(where_conditions)
            
            # Build relationship pattern
            if relationship_types:
                rel_type = "|".join(relationship_types)
                rel_pattern = f"[:{rel_type}*1..{depth}]"
            else:
                rel_pattern = f"[*1..{depth}]"
            
            # Build direction pattern
            if direction == "incoming":
                direction_pattern = f"<-{rel_pattern}-"
            elif direction == "outgoing":
                direction_pattern = f"-{rel_pattern}->"
            else:  # both
                direction_pattern = f"-{rel_pattern}-"
            
            query += f" MATCH (n){direction_pattern}(neighbor) RETURN DISTINCT neighbor"
            
            result = conn.execute_query(query, params)
            conn.close()
            
            return [TextContent(type="text", text=f"Neighbors:\n{json.dumps(result, indent=2)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting neighbors: {str(e)}")]

# 5. Schema Management Tools
class CreateIndexToolHandler(Neo4jToolHandler):
    def __init__(self):
        super().__init__("create_index")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Create an index on node properties",
            inputSchema={
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "description": "Node label for the index"
                    },
                    "property": {
                        "type": "string",
                        "description": "Property name for the index"
                    },
                    "index_name": {
                        "type": "string",
                        "description": "Custom name for the index (optional)"
                    }
                },
                "required": ["label", "property"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            conn = self.get_connection(credentials)
            
            label = args["label"]
            property_name = args["property"]
            index_name = args.get("index_name")
            
            if index_name:
                query = f"CREATE INDEX {index_name} FOR (n:{label}) ON (n.{property_name})"
            else:
                query = f"CREATE INDEX FOR (n:{label}) ON (n.{property_name})"
            
            result = conn.execute_query(query)
            conn.close()
            
            return [TextContent(type="text", text=f"Index created:\n{json.dumps(result, indent=2)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error creating index: {str(e)}")]

class CreateConstraintToolHandler(Neo4jToolHandler):
    def __init__(self):
        super().__init__("create_constraint")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Create a constraint on node properties",
            inputSchema={
                "type": "object",
                "properties": {
                    "constraint_type": {
                        "type": "string",
                        "enum": ["UNIQUE", "NODE_KEY", "EXISTS"],
                        "description": "Type of constraint"
                    },
                    "label": {
                        "type": "string",
                        "description": "Node label for the constraint"
                    },
                    "properties": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Property names for the constraint"
                    },
                    "constraint_name": {
                        "type": "string",
                        "description": "Custom name for the constraint (optional)"
                    }
                },
                "required": ["constraint_type", "label", "properties"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            conn = self.get_connection(credentials)
            
            constraint_type = args["constraint_type"]
            label = args["label"]
            properties = args["properties"]
            constraint_name = args.get("constraint_name")
            
            properties_str = ", ".join([f"n.{prop}" for prop in properties])
            
            if constraint_name:
                query = f"CREATE CONSTRAINT {constraint_name} FOR (n:{label}) REQUIRE "
            else:
                query = f"CREATE CONSTRAINT FOR (n:{label}) REQUIRE "
            
            if constraint_type == "UNIQUE":
                query += f"({properties_str}) IS UNIQUE"
            elif constraint_type == "NODE_KEY":
                query += f"({properties_str}) IS NODE KEY"
            elif constraint_type == "EXISTS":
                query += f"{properties_str} IS NOT NULL"
            
            result = conn.execute_query(query)
            conn.close()
            
            return [TextContent(type="text", text=f"Constraint created:\n{json.dumps(result, indent=2)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error creating constraint: {str(e)}")]

# 6. Data Import/Export Tools
class ImportCSVToolHandler(Neo4jToolHandler):
    def __init__(self):
        super().__init__("import_csv")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Import data from CSV file into Neo4j",
            inputSchema={
                "type": "object",
                "properties": {
                    "csv_url": {
                        "type": "string",
                        "description": "URL or file path to CSV file"
                    },
                    "create_nodes": {
                        "type": "boolean",
                        "description": "Whether to create nodes from CSV data",
                        "default": True
                    },
                    "node_label": {
                        "type": "string",
                        "description": "Label for created nodes (if creating nodes)"
                    },
                    "id_column": {
                        "type": "string",
                        "description": "Column name to use as node identifier"
                    },
                    "skip_lines": {
                        "type": "integer",
                        "description": "Number of lines to skip at beginning",
                        "default": 1
                    }
                },
                "required": ["csv_url"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            conn = self.get_connection(credentials)
            
            csv_url = args["csv_url"]
            create_nodes = args.get("create_nodes", True)
            node_label = args.get("node_label", "ImportedNode")
            id_column = args.get("id_column", "id")
            skip_lines = args.get("skip_lines", 1)
            
            if create_nodes:
                query = f"""
                LOAD CSV WITH HEADERS FROM '{csv_url}' AS row
                SKIP {skip_lines}
                CREATE (n:{node_label})
                SET n = row
                RETURN count(n) as nodes_created
                """
            else:
                query = f"""
                LOAD CSV WITH HEADERS FROM '{csv_url}' AS row
                SKIP {skip_lines}
                RETURN count(row) as rows_processed
                """
            
            result = conn.execute_query(query)
            conn.close()
            
            return [TextContent(type="text", text=f"CSV import completed:\n{json.dumps(result, indent=2)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error importing CSV: {str(e)}")]

# 7. Custom Cypher Query Tool
class ExecuteCypherToolHandler(Neo4jToolHandler):
    def __init__(self):
        super().__init__("execute_cypher")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Execute a custom Cypher query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Cypher query to execute"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Parameters for the query (optional)"
                    },
                    "read_only": {
                        "type": "boolean",
                        "description": "Whether this is a read-only query",
                        "default": False
                    },
                    "force_execute": {
                        "type": "boolean",
                        "description": "Force execution of potentially destructive operations without warnings",
                        "default": False
                    }
                },
                "required": ["query"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            conn = self.get_connection(credentials)
            
            query = args["query"]
            parameters = args.get("parameters", {})
            read_only = args.get("read_only", False)
            force_execute = args.get("force_execute", False)
            
            # Basic safety check for destructive operations
            dangerous_keywords = ["DROP", "DELETE", "REMOVE", "DETACH DELETE"]
            if not read_only and not force_execute:
                query_upper = query.upper()
                for keyword in dangerous_keywords:
                    if keyword in query_upper:
                        # Still execute but with a warning message
                        result = conn.execute_query(query, parameters)
                        conn.close()
                        return [TextContent(type="text", text=f"WARNING: Destructive operation executed. Query contained '{keyword}'.\n\nQuery result:\n{json.dumps(result, indent=2)}")]
            
            result = conn.execute_query(query, parameters)
            conn.close()
            
            return [TextContent(type="text", text=f"Query result:\n{json.dumps(result, indent=2)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error executing query: {str(e)}")]

# 8. Performance and Monitoring Tools
class ExplainQueryToolHandler(Neo4jToolHandler):
    def __init__(self):
        super().__init__("explain_query")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Get execution plan for a Cypher query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Cypher query to explain"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Parameters for the query (optional)"
                    }
                },
                "required": ["query"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            conn = self.get_connection(credentials)
            
            query = args["query"]
            parameters = args.get("parameters", {})
            
            explain_query = f"EXPLAIN {query}"
            result = conn.execute_query(explain_query, parameters)
            conn.close()
            
            return [TextContent(type="text", text=f"Query execution plan:\n{json.dumps(result, indent=2)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error explaining query: {str(e)}")]

class ProfileQueryToolHandler(Neo4jToolHandler):
    def __init__(self):
        super().__init__("profile_query")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Profile a Cypher query execution",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Cypher query to profile"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Parameters for the query (optional)"
                    }
                },
                "required": ["query"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            credentials = args.get("__credentials__", {})
            conn = self.get_connection(credentials)
            
            query = args["query"]
            parameters = args.get("parameters", {})
            
            profile_query = f"PROFILE {query}"
            result = conn.execute_query(profile_query, parameters)
            conn.close()
            
            return [TextContent(type="text", text=f"Query profile:\n{json.dumps(result, indent=2)}")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error profiling query: {str(e)}")]

# Tool registry
tool_handlers: Dict[str, Neo4jToolHandler] = {}

def add_tool_handler(tool_class: Neo4jToolHandler):
    """Register a tool handler"""
    global tool_handlers
    tool_handlers[tool_class.name] = tool_class

def get_tool_handler(name: str) -> Optional[Neo4jToolHandler]:
    """Retrieve a tool handler by name"""
    return tool_handlers.get(name)

# Register all tool handlers
add_tool_handler(DatabaseInfoToolHandler())
add_tool_handler(ListConstraintsToolHandler())
add_tool_handler(ListIndexesToolHandler())
add_tool_handler(ListLabelsToolHandler())
add_tool_handler(CreateNodeToolHandler())
add_tool_handler(FindNodesToolHandler())
add_tool_handler(UpdateNodeToolHandler())
add_tool_handler(DeleteNodeToolHandler())
add_tool_handler(CreateRelationshipToolHandler())
add_tool_handler(FindRelationshipsToolHandler())
add_tool_handler(ShortestPathToolHandler())
add_tool_handler(GetNeighborsToolHandler())
add_tool_handler(CreateIndexToolHandler())
add_tool_handler(CreateConstraintToolHandler())
add_tool_handler(ImportCSVToolHandler())
add_tool_handler(ExecuteCypherToolHandler())
add_tool_handler(ExplainQueryToolHandler())
add_tool_handler(ProfileQueryToolHandler())

@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List all available Neo4j tools"""
    return [th.get_tool_description() for th in tool_handlers.values()]

@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls for Neo4j operations"""
    try:
        tool_handler = get_tool_handler(name)
        if not tool_handler:
            raise ValueError(f"Unknown tool: {name}")
        
        return tool_handler.run_tool(arguments)
        
    except Exception as e:
        logger.error(f"Error during call_tool: {str(e)}")
        logger.error(traceback.format_exc())
        return [TextContent(type="text", text=f"Error in {name}: {str(e)}")]

@app.list_resources()
async def handle_list_resources() -> List[types.Resource]:
    """List available resources"""
    return [
        types.Resource(
            uri="neo4j://operations",
            name="Neo4j Operations",
            description="Available graph database operations using Neo4j",
            mimeType="text/plain"
        ),
        types.Resource(
            uri="neo4j://cypher-examples",
            name="Cypher Query Examples",
            description="Common Cypher query patterns and examples",
            mimeType="text/plain"
        )
    ]

@app.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read resource content"""
    if uri == "neo4j://operations":
        operations = [
            "Database Management: Get database info, list constraints, list indexes",
            "Node Operations: Create, find, update, delete nodes",
            "Relationship Operations: Create, find relationships",
            "Graph Analysis: Shortest path, neighbors, graph traversal",
            "Schema Management: Create indexes, constraints",
            "Data Import/Export: CSV import, data migration",
            "Query Operations: Execute custom Cypher, explain plans, profiling",
            "Performance Monitoring: Query optimization, performance analysis"
        ]
        return "\n".join(operations)
    elif uri == "neo4j://cypher-examples":
        examples = [
            "# Node Creation",
            "CREATE (p:Person {name: 'Alice', age: 30})",
            "",
            "# Relationship Creation", 
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})",
            "CREATE (a)-[:KNOWS]->(b)",
            "",
            "# Finding Patterns",
            "MATCH (p:Person)-[:KNOWS]->(friend:Person)",
            "RETURN p.name, friend.name",
            "",
            "# Shortest Path",
            "MATCH path = shortestPath((a:Person {name: 'Alice'})-[*]-(b:Person {name: 'Charlie'}))",
            "RETURN path",
            "",
            "# Aggregation",
            "MATCH (p:Person)-[:KNOWS]->(friend)",
            "RETURN p.name, count(friend) as friendCount",
            "ORDER BY friendCount DESC"
        ]
        return "\n".join(examples)
    else:
        raise ValueError(f"Unknown resource: {uri}")

async def main():
    """Main function to run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
