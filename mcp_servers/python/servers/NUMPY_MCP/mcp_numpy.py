import asyncio
import json
from typing import Any, Dict, List, Optional, Union
import numpy as np
from fastapi import FastAPI, HTTPException, Query, Header, Depends
from pydantic import BaseModel, Field
import uvicorn
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
import mcp.server.stdio
import mcp.types as types

# FastAPI app for REST API testing
app = FastAPI(
    title="NumPy MCP Server",
    description="Mathematical operations using NumPy - REST API + MCP Protocol",
    version="1.0.0"
)

# MCP server instance
mcp_server = Server("numpy-mcp")

# Pydantic Models for REST API
class MatrixInput(BaseModel):
    matrix: List[List[float]] = Field(..., description="2D matrix as nested lists")

class TwoMatrixInput(BaseModel):
    matrix_a: List[List[float]] = Field(..., description="First matrix")
    matrix_b: List[List[float]] = Field(..., description="Second matrix")

class VectorInput(BaseModel):
    vector: List[float] = Field(..., description="1D vector")

class LinearSystemInput(BaseModel):
    matrix_a: List[List[float]] = Field(..., description="Coefficient matrix A")
    vector_b: List[float] = Field(..., description="Constants vector b")

class ReshapeInput(BaseModel):
    matrix: List[List[float]] = Field(..., description="Input matrix")
    new_shape: List[int] = Field(..., description="Target shape [rows, cols]")

class PolynomialInput(BaseModel):
    coefficients: List[float] = Field(..., description="Polynomial coefficients (highest degree first)")

class NormInput(BaseModel):
    matrix: List[List[float]] = Field(..., description="Matrix or vector")
    ord: Optional[Union[str, int, float]] = Field("fro", description="Order of norm")

# API Key validation for REST endpoints
def validate_api_key(
    api_key: Optional[str] = Query(None, description="API key as query parameter"),
    authorization: Optional[str] = Header(None, description="Bearer token in header")
) -> str:
    """Validate API key from query param or Authorization header"""
    key = None
    
    if api_key:
        key = api_key
    elif authorization and authorization.startswith("Bearer "):
        key = authorization[7:]
    
    if not key:
        raise HTTPException(status_code=401, detail="Unauthorized: API key required.")
    
    return key

# Helper functions
def safe_numpy_array(data) -> np.ndarray:
    """Safely convert to numpy array"""
    try:
        return np.array(data, dtype=float)
    except Exception as e:
        raise ValueError(f"Invalid array format: {str(e)}")

def format_result(result: np.ndarray, operation: str) -> dict:
    """Format numpy result for JSON response"""
    if result.ndim == 0:
        return {"result": float(result), "operation": operation}
    else:
        return {"result": result.tolist(), "operation": operation}

# REST API ENDPOINTS

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "NumPy MCP Server"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "NumPy MCP Server - REST API + MCP Protocol",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0"
    }

# Basic Math Operations
@app.post("/api/matrix/add")
async def add_matrices(
    data: TwoMatrixInput,
    api_key: str = Depends(validate_api_key)
):
    """Add two matrices element-wise"""
    try:
        a = safe_numpy_array(data.matrix_a)
        b = safe_numpy_array(data.matrix_b)
        result = np.add(a, b)
        return format_result(result, "matrix_addition")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/matrix/subtract")
async def subtract_matrices(
    data: TwoMatrixInput,
    api_key: str = Depends(validate_api_key)
):
    """Subtract matrix B from matrix A"""
    try:
        a = safe_numpy_array(data.matrix_a)
        b = safe_numpy_array(data.matrix_b)
        result = np.subtract(a, b)
        return format_result(result, "matrix_subtraction")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/matrix/multiply")
async def multiply_matrices(
    data: TwoMatrixInput,
    api_key: str = Depends(validate_api_key)
):
    """Matrix multiplication"""
    try:
        a = safe_numpy_array(data.matrix_a)
        b = safe_numpy_array(data.matrix_b)
        result = np.matmul(a, b)
        return format_result(result, "matrix_multiplication")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/matrix/element_multiply")
async def element_wise_multiply(
    data: TwoMatrixInput,
    api_key: str = Depends(validate_api_key)
):
    """Element-wise multiplication"""
    try:
        a = safe_numpy_array(data.matrix_a)
        b = safe_numpy_array(data.matrix_b)
        result = np.multiply(a, b)
        return format_result(result, "element_wise_multiplication")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/matrix/dot")
async def dot_product(
    data: TwoMatrixInput,
    api_key: str = Depends(validate_api_key)
):
    """Dot product"""
    try:
        a = safe_numpy_array(data.matrix_a)
        b = safe_numpy_array(data.matrix_b)
        result = np.dot(a, b)
        return format_result(result, "dot_product")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Linear Algebra Operations
@app.post("/api/matrix/transpose")
async def transpose_matrix(
    data: MatrixInput,
    api_key: str = Depends(validate_api_key)
):
    """Transpose a matrix"""
    try:
        matrix = safe_numpy_array(data.matrix)
        result = np.transpose(matrix)
        return format_result(result, "matrix_transpose")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/matrix/inverse")
async def matrix_inverse(
    data: MatrixInput,
    api_key: str = Depends(validate_api_key)
):
    """Calculate matrix inverse"""
    try:
        matrix = safe_numpy_array(data.matrix)
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError("Matrix must be square for inverse")
        result = np.linalg.inv(matrix)
        return format_result(result, "matrix_inverse")
    except np.linalg.LinAlgError:
        raise HTTPException(status_code=400, detail="Matrix is singular and cannot be inverted")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/matrix/determinant")
async def matrix_determinant(
    data: MatrixInput,
    api_key: str = Depends(validate_api_key)
):
    """Calculate matrix determinant"""
    try:
        matrix = safe_numpy_array(data.matrix)
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError("Matrix must be square for determinant")
        result = np.linalg.det(matrix)
        return {"result": float(result), "operation": "matrix_determinant"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/linear/solve")
async def solve_linear_system(
    data: LinearSystemInput,
    api_key: str = Depends(validate_api_key)
):
    """Solve linear system Ax = b"""
    try:
        a = safe_numpy_array(data.matrix_a)
        b = safe_numpy_array(data.vector_b)
        result = np.linalg.solve(a, b)
        return format_result(result, "linear_system_solution")
    except np.linalg.LinAlgError:
        raise HTTPException(status_code=400, detail="Linear system has no unique solution")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/matrix/eigen")
async def eigenvalues_eigenvectors(
    data: MatrixInput,
    api_key: str = Depends(validate_api_key)
):
    """Calculate eigenvalues and eigenvectors"""
    try:
        matrix = safe_numpy_array(data.matrix)
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError("Matrix must be square for eigenvalue decomposition")
        eigenvalues, eigenvectors = np.linalg.eig(matrix)
        return {
            "eigenvalues": eigenvalues.tolist(),
            "eigenvectors": eigenvectors.tolist(),
            "operation": "eigenvalue_decomposition"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Advanced Operations
@app.post("/api/signal/fft")
async def fast_fourier_transform(
    data: VectorInput,
    api_key: str = Depends(validate_api_key)
):
    """Fast Fourier Transform"""
    try:
        vector = safe_numpy_array(data.vector)
        result = np.fft.fft(vector)
        # Convert complex numbers for JSON
        result_list = [{"real": float(x.real), "imag": float(x.imag)} for x in result]
        return {"result": result_list, "operation": "fft"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/matrix/reshape")
async def reshape_matrix(
    data: ReshapeInput,
    api_key: str = Depends(validate_api_key)
):
    """Reshape matrix to new dimensions"""
    try:
        matrix = safe_numpy_array(data.matrix)
        result = np.reshape(matrix, data.new_shape)
        return format_result(result, "matrix_reshape")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/matrix/norm")
async def matrix_norm(
    data: NormInput,
    api_key: str = Depends(validate_api_key)
):
    """Calculate matrix/vector norm"""
    try:
        matrix = safe_numpy_array(data.matrix)
        result = np.linalg.norm(matrix, ord=data.ord)
        return {"result": float(result), "operation": f"matrix_norm_{data.ord}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/polynomial/roots")
async def polynomial_roots(
    data: PolynomialInput,
    api_key: str = Depends(validate_api_key)
):
    """Find roots of polynomial"""
    try:
        coeffs = safe_numpy_array(data.coefficients)
        roots = np.roots(coeffs)
        # Handle complex roots
        result_list = []
        for root in roots:
            if np.isreal(root):
                result_list.append(float(root.real))
            else:
                result_list.append({"real": float(root.real), "imag": float(root.imag)})
        return {"result": result_list, "operation": "polynomial_roots"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Statistical Operations
@app.post("/api/stats/mean")
async def calculate_mean(
    data: MatrixInput,
    api_key: str = Depends(validate_api_key)
):
    """Calculate mean of matrix"""
    try:
        matrix = safe_numpy_array(data.matrix)
        result = np.mean(matrix)
        return {"result": float(result), "operation": "matrix_mean"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/stats/std")
async def calculate_std(
    data: MatrixInput,
    api_key: str = Depends(validate_api_key)
):
    """Calculate standard deviation of matrix"""
    try:
        matrix = safe_numpy_array(data.matrix)
        result = np.std(matrix)
        return {"result": float(result), "operation": "matrix_std"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# MCP Protocol Implementation
@mcp_server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List all available NumPy tools for MCP"""
    return [
        Tool(
            name="matrix_add",
            description="Add two matrices element-wise",
            inputSchema={
                "type": "object",
                "properties": {
                    "matrix_a": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}},
                    "matrix_b": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}}
                },
                "required": ["matrix_a", "matrix_b"]
            }
        ),
        Tool(
            name="matrix_multiply",
            description="Multiply two matrices",
            inputSchema={
                "type": "object",
                "properties": {
                    "matrix_a": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}},
                    "matrix_b": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}}
                },
                "required": ["matrix_a", "matrix_b"]
            }
        ),
        Tool(
            name="matrix_transpose",
            description="Transpose a matrix",
            inputSchema={
                "type": "object",
                "properties": {
                    "matrix": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}}
                },
                "required": ["matrix"]
            }
        ),
        Tool(
            name="matrix_inverse",
            description="Calculate matrix inverse",
            inputSchema={
                "type": "object",
                "properties": {
                    "matrix": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}}
                },
                "required": ["matrix"]
            }
        ),
        Tool(
            name="solve_linear_system",
            description="Solve linear system Ax = b",
            inputSchema={
                "type": "object",
                "properties": {
                    "matrix_a": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}},
                    "vector_b": {"type": "array", "items": {"type": "number"}}
                },
                "required": ["matrix_a", "vector_b"]
            }
        ),
        Tool(
            name="eigenvalues_eigenvectors",
            description="Calculate eigenvalues and eigenvectors",
            inputSchema={
                "type": "object",
                "properties": {
                    "matrix": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}}
                },
                "required": ["matrix"]
            }
        ),
        Tool(
            name="fft",
            description="Fast Fourier Transform",
            inputSchema={
                "type": "object",
                "properties": {
                    "vector": {"type": "array", "items": {"type": "number"}}
                },
                "required": ["vector"]
            }
        ),
        Tool(
            name="polynomial_roots",
            description="Find roots of polynomial",
            inputSchema={
                "type": "object",
                "properties": {
                    "coefficients": {"type": "array", "items": {"type": "number"}}
                },
                "required": ["coefficients"]
            }
        )
    ]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls for NumPy operations"""
    try:
        if name == "matrix_add":
            matrix_a = safe_numpy_array(arguments["matrix_a"])
            matrix_b = safe_numpy_array(arguments["matrix_b"])
            result = np.add(matrix_a, matrix_b)
            return [types.TextContent(type="text", text=f"Matrix Addition Result:\n{result.tolist()}")]
        
        elif name == "matrix_multiply":
            matrix_a = safe_numpy_array(arguments["matrix_a"])
            matrix_b = safe_numpy_array(arguments["matrix_b"])
            result = np.matmul(matrix_a, matrix_b)
            return [types.TextContent(type="text", text=f"Matrix Multiplication Result:\n{result.tolist()}")]
        
        elif name == "matrix_transpose":
            matrix = safe_numpy_array(arguments["matrix"])
            result = np.transpose(matrix)
            return [types.TextContent(type="text", text=f"Matrix Transpose Result:\n{result.tolist()}")]
        
        elif name == "matrix_inverse":
            matrix = safe_numpy_array(arguments["matrix"])
            if matrix.shape[0] != matrix.shape[1]:
                raise ValueError("Matrix must be square for inverse")
            result = np.linalg.inv(matrix)
            return [types.TextContent(type="text", text=f"Matrix Inverse Result:\n{result.tolist()}")]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error in {name}: {str(e)}")]

@mcp_server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available resources"""
    return [
        Resource(
            uri="numpy://operations",
            name="NumPy Operations",
            description="Available mathematical operations using NumPy",
            mimeType="text/plain"
        )
    ]

@mcp_server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read resource content"""
    if uri == "numpy://operations":
        return "NumPy Mathematical Operations: Matrix operations, Linear algebra, Signal processing, Statistics"
    else:
        raise ValueError(f"Unknown resource: {uri}")

# Run functions
async def run_mcp_server():
    """Run MCP server via stdio"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await mcp_server.run(read_stream, write_stream, mcp_server.create_initialization_options())

def run_rest_server():
    """Run REST API server"""
    uvicorn.run(app, host="0.0.0.0", port=8010)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--mcp":
        asyncio.run(run_mcp_server())
    else:
        run_rest_server()
