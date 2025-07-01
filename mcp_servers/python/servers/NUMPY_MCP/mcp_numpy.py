import logging
from collections.abc import Sequence
from typing import Any, Dict, List, Optional
import numpy as np
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("numpy-mcp")

# MCP server instance
app = Server("numpy-mcp")

# Helper functions
def safe_numpy_array(data) -> np.ndarray:
    """Safely convert to numpy array"""
    try:
        return np.array(data, dtype=float)
    except Exception as e:
        raise ValueError(f"Invalid array format: {str(e)}")

def format_complex_result(result):
    """Format complex numbers for JSON serialization"""
    if np.iscomplexobj(result):
        if result.ndim == 0:
            return {"real": float(result.real), "imag": float(result.imag)}
        else:
            return [{"real": float(x.real), "imag": float(x.imag)} for x in result.flatten()]
    return result.tolist() if hasattr(result, 'tolist') else result

# Tool handler base class
class NumPyToolHandler:
    def __init__(self, name: str):
        self.name = name

    def get_tool_description(self) -> Tool:
        raise NotImplementedError()

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        raise NotImplementedError()

# Basic Matrix Operations
class MatrixAddToolHandler(NumPyToolHandler):
    def __init__(self):
        super().__init__("matrix_add")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Add two matrices element-wise",
            inputSchema={
                "type": "object",
                "properties": {
                    "matrix_a": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "First matrix as nested array"
                    },
                    "matrix_b": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "Second matrix as nested array"
                    }
                },
                "required": ["matrix_a", "matrix_b"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            matrix_a = safe_numpy_array(args["matrix_a"])
            matrix_b = safe_numpy_array(args["matrix_b"])
            result = np.add(matrix_a, matrix_b)
            return [TextContent(type="text", text=f"Matrix Addition Result:\n{result.tolist()}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in matrix addition: {str(e)}")]

class MatrixMultiplyToolHandler(NumPyToolHandler):
    def __init__(self):
        super().__init__("matrix_multiply")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Multiply two matrices using matrix multiplication",
            inputSchema={
                "type": "object",
                "properties": {
                    "matrix_a": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "First matrix"
                    },
                    "matrix_b": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "Second matrix"
                    }
                },
                "required": ["matrix_a", "matrix_b"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            matrix_a = safe_numpy_array(args["matrix_a"])
            matrix_b = safe_numpy_array(args["matrix_b"])
            result = np.matmul(matrix_a, matrix_b)
            return [TextContent(type="text", text=f"Matrix Multiplication Result:\n{result.tolist()}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in matrix multiplication: {str(e)}")]

class MatrixSubtractToolHandler(NumPyToolHandler):
    def __init__(self):
        super().__init__("matrix_subtract")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Subtract two matrices element-wise",
            inputSchema={
                "type": "object",
                "properties": {
                    "matrix_a": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "First matrix"
                    },
                    "matrix_b": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "Second matrix to subtract from first"
                    }
                },
                "required": ["matrix_a", "matrix_b"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            matrix_a = safe_numpy_array(args["matrix_a"])
            matrix_b = safe_numpy_array(args["matrix_b"])
            result = np.subtract(matrix_a, matrix_b)
            return [TextContent(type="text", text=f"Matrix Subtraction Result:\n{result.tolist()}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in matrix subtraction: {str(e)}")]

class ElementWiseMultiplyToolHandler(NumPyToolHandler):
    def __init__(self):
        super().__init__("element_wise_multiply")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Element-wise multiplication of two matrices",
            inputSchema={
                "type": "object",
                "properties": {
                    "matrix_a": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "First matrix"
                    },
                    "matrix_b": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "Second matrix"
                    }
                },
                "required": ["matrix_a", "matrix_b"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            matrix_a = safe_numpy_array(args["matrix_a"])
            matrix_b = safe_numpy_array(args["matrix_b"])
            result = np.multiply(matrix_a, matrix_b)
            return [TextContent(type="text", text=f"Element-wise Multiplication Result:\n{result.tolist()}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in element-wise multiplication: {str(e)}")]

class DotProductToolHandler(NumPyToolHandler):
    def __init__(self):
        super().__init__("dot_product")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Dot product of two matrices/vectors",
            inputSchema={
                "type": "object",
                "properties": {
                    "matrix_a": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "First matrix/vector"
                    },
                    "matrix_b": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "Second matrix/vector"
                    }
                },
                "required": ["matrix_a", "matrix_b"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            matrix_a = safe_numpy_array(args["matrix_a"])
            matrix_b = safe_numpy_array(args["matrix_b"])
            result = np.dot(matrix_a, matrix_b)
            return [TextContent(type="text", text=f"Dot Product Result:\n{result.tolist() if hasattr(result, 'tolist') else result}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in dot product: {str(e)}")]

class MatrixTransposeToolHandler(NumPyToolHandler):
    def __init__(self):
        super().__init__("matrix_transpose")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Transpose a matrix",
            inputSchema={
                "type": "object",
                "properties": {
                    "matrix": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "Matrix to transpose"
                    }
                },
                "required": ["matrix"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            matrix = safe_numpy_array(args["matrix"])
            result = np.transpose(matrix)
            return [TextContent(type="text", text=f"Matrix Transpose Result:\n{result.tolist()}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in matrix transpose: {str(e)}")]

class MatrixInverseToolHandler(NumPyToolHandler):
    def __init__(self):
        super().__init__("matrix_inverse")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Calculate matrix inverse",
            inputSchema={
                "type": "object",
                "properties": {
                    "matrix": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "Square matrix to invert"
                    }
                },
                "required": ["matrix"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            matrix = safe_numpy_array(args["matrix"])
            if matrix.shape[0] != matrix.shape[1]:
                raise ValueError("Matrix must be square for inverse")
            result = np.linalg.inv(matrix)
            return [TextContent(type="text", text=f"Matrix Inverse Result:\n{result.tolist()}")]
        except np.linalg.LinAlgError:
            return [TextContent(type="text", text="Error: Matrix is singular and cannot be inverted")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in matrix inverse: {str(e)}")]

class MatrixDeterminantToolHandler(NumPyToolHandler):
    def __init__(self):
        super().__init__("matrix_determinant")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Calculate matrix determinant",
            inputSchema={
                "type": "object",
                "properties": {
                    "matrix": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "Square matrix"
                    }
                },
                "required": ["matrix"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            matrix = safe_numpy_array(args["matrix"])
            if matrix.shape[0] != matrix.shape[1]:
                raise ValueError("Matrix must be square for determinant")
            result = np.linalg.det(matrix)
            return [TextContent(type="text", text=f"Matrix Determinant: {float(result)}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in determinant calculation: {str(e)}")]

class SolveLinearSystemToolHandler(NumPyToolHandler):
    def __init__(self):
        super().__init__("solve_linear_system")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Solve linear system Ax = b",
            inputSchema={
                "type": "object",
                "properties": {
                    "matrix_a": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "Coefficient matrix A"
                    },
                    "vector_b": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Constants vector b"
                    }
                },
                "required": ["matrix_a", "vector_b"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            matrix_a = safe_numpy_array(args["matrix_a"])
            vector_b = safe_numpy_array(args["vector_b"])
            result = np.linalg.solve(matrix_a, vector_b)
            return [TextContent(type="text", text=f"Linear System Solution:\nx = {result.tolist()}")]
        except np.linalg.LinAlgError:
            return [TextContent(type="text", text="Error: Linear system has no unique solution")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error solving linear system: {str(e)}")]

class EigenDecompositionToolHandler(NumPyToolHandler):
    def __init__(self):
        super().__init__("eigenvalues_eigenvectors")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Calculate eigenvalues and eigenvectors",
            inputSchema={
                "type": "object",
                "properties": {
                    "matrix": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "Square matrix"
                    }
                },
                "required": ["matrix"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            matrix = safe_numpy_array(args["matrix"])
            if matrix.shape[0] != matrix.shape[1]:
                raise ValueError("Matrix must be square for eigenvalue decomposition")
            eigenvalues, eigenvectors = np.linalg.eig(matrix)
            return [TextContent(
                type="text",
                text=f"Eigenvalues: {format_complex_result(eigenvalues)}\nEigenvectors:\n{format_complex_result(eigenvectors)}"
            )]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in eigenvalue decomposition: {str(e)}")]

class SVDToolHandler(NumPyToolHandler):
    def __init__(self):
        super().__init__("singular_value_decomposition")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Singular Value Decomposition",
            inputSchema={
                "type": "object",
                "properties": {
                    "matrix": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "Matrix for SVD"
                    }
                },
                "required": ["matrix"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            matrix = safe_numpy_array(args["matrix"])
            U, s, Vt = np.linalg.svd(matrix)
            return [TextContent(
                type="text",
                text=f"SVD Decomposition:\nU matrix:\n{U.tolist()}\nSingular values: {s.tolist()}\nVt matrix:\n{Vt.tolist()}"
            )]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in SVD: {str(e)}")]

class QRDecompositionToolHandler(NumPyToolHandler):
    def __init__(self):
        super().__init__("qr_decomposition")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="QR Decomposition",
            inputSchema={
                "type": "object",
                "properties": {
                    "matrix": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "Matrix for QR decomposition"
                    }
                },
                "required": ["matrix"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            matrix = safe_numpy_array(args["matrix"])
            Q, R = np.linalg.qr(matrix)
            return [TextContent(
                type="text",
                text=f"QR Decomposition:\nQ matrix:\n{Q.tolist()}\nR matrix:\n{R.tolist()}"
            )]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in QR decomposition: {str(e)}")]

class MatrixPowerToolHandler(NumPyToolHandler):
    def __init__(self):
        super().__init__("matrix_power")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Raise matrix to a power",
            inputSchema={
                "type": "object",
                "properties": {
                    "matrix": {
                        "type": "array",
                        "items": {
                            "type": "array", 
                            "items": {"type": "number"}
                        },
                        "description": "First matrix as nested array"
                    },
                    "power": {
                        "type": "integer",
                        "description": "Power to raise matrix to"
                    }
                },
                "required": ["matrix", "power"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            matrix = safe_numpy_array(args["matrix"])
            power = args["power"]
            if matrix.shape[0] != matrix.shape[1]:
                raise ValueError("Matrix must be square for matrix power")
            result = np.linalg.matrix_power(matrix, power)
            return [TextContent(type="text", text=f"Matrix Power {power} Result:\n{result.tolist()}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in matrix power: {str(e)}")]

class FFTToolHandler(NumPyToolHandler):
    def __init__(self):
        super().__init__("fast_fourier_transform")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Fast Fourier Transform",
            inputSchema={
                "type": "object",
                "properties": {
                    "vector": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Input vector for FFT"
                    }
                },
                "required": ["vector"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            vector = safe_numpy_array(args["vector"])
            result = np.fft.fft(vector)
            formatted_result = format_complex_result(result)
            return [TextContent(type="text", text=f"FFT Result: {formatted_result}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in FFT: {str(e)}")]

class PolynomialRootsToolHandler(NumPyToolHandler):
    def __init__(self):
        super().__init__("polynomial_roots")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Find roots of polynomial",
            inputSchema={
                "type": "object",
                "properties": {
                    "coefficients": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Polynomial coefficients (highest degree first)"
                    }
                },
                "required": ["coefficients"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            coefficients = safe_numpy_array(args["coefficients"])
            roots = np.roots(coefficients)
            formatted_roots = format_complex_result(roots)
            return [TextContent(type="text", text=f"Polynomial Roots: {formatted_roots}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error finding polynomial roots: {str(e)}")]

class StatisticsToolHandler(NumPyToolHandler):
    def __init__(self):
        super().__init__("calculate_statistics")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Calculate statistical measures (mean, std, variance, min, max, median)",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "Data matrix or vector"
                    },
                    "operations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of operations: mean, std, var, min, max, median",
                        "default": ["mean", "std"]
                    }
                },
                "required": ["data"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            data = safe_numpy_array(args["data"])
            operations = args.get("operations", ["mean", "std"])
            
            results = []
            for op in operations:
                if op == "mean":
                    results.append(f"Mean: {float(np.mean(data))}")
                elif op == "std":
                    results.append(f"Standard Deviation: {float(np.std(data))}")
                elif op == "var":
                    results.append(f"Variance: {float(np.var(data))}")
                elif op == "min":
                    results.append(f"Minimum: {float(np.min(data))}")
                elif op == "max":
                    results.append(f"Maximum: {float(np.max(data))}")
                elif op == "median":
                    results.append(f"Median: {float(np.median(data))}")
            
            return [TextContent(type="text", text=f"Statistical Results:\n" + "\n".join(results))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in statistics calculation: {str(e)}")]

class NumericalDerivativeToolHandler(NumPyToolHandler):
    def __init__(self):
        super().__init__("numerical_derivative")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Calculate numerical derivative using numpy gradient",
            inputSchema={
                "type": "object",
                "properties": {
                    "vector": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Input vector for derivative"
                    }
                },
                "required": ["vector"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            vector = safe_numpy_array(args["vector"])
            result = np.gradient(vector)
            return [TextContent(type="text", text=f"Numerical Derivative:\n{result.tolist()}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in numerical derivative: {str(e)}")]

class ConvolutionToolHandler(NumPyToolHandler):
    def __init__(self):
        super().__init__("convolution")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Convolution of two signals",
            inputSchema={
                "type": "object",
                "properties": {
                    "signal1": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "First signal"
                    },
                    "signal2": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Second signal"
                    }
                },
                "required": ["signal1", "signal2"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            signal1 = safe_numpy_array(args["signal1"])
            signal2 = safe_numpy_array(args["signal2"])
            result = np.convolve(signal1, signal2, mode='full')
            return [TextContent(type="text", text=f"Convolution Result:\n{result.tolist()}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error in convolution: {str(e)}")]

class RandomGeneratorToolHandler(NumPyToolHandler):
    def __init__(self):
        super().__init__("generate_random_normal")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Generate random numbers from normal distribution",
            inputSchema={
                "type": "object",
                "properties": {
                    "mean": {
                        "type": "number",
                        "description": "Mean of distribution",
                        "default": 0.0
                    },
                    "std": {
                        "type": "number",
                        "description": "Standard deviation",
                        "default": 1.0
                    },
                    "size": {
                        "type": "integer",
                        "description": "Number of samples",
                        "default": 10
                    }
                }
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent]:
        try:
            mean = args.get("mean", 0.0)
            std = args.get("std", 1.0)
            size = args.get("size", 10)
            result = np.random.normal(mean, std, size)
            return [TextContent(type="text", text=f"Random Normal Distribution (mean={mean}, std={std}):\n{result.tolist()}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error generating random numbers: {str(e)}")]

# Tool registry
tool_handlers: Dict[str, NumPyToolHandler] = {}

def add_tool_handler(tool_class: NumPyToolHandler):
    """Register a tool handler"""
    global tool_handlers
    tool_handlers[tool_class.name] = tool_class

def get_tool_handler(name: str) -> Optional[NumPyToolHandler]:
    """Retrieve a tool handler by name"""
    return tool_handlers.get(name)

# Register all tool handlers
add_tool_handler(MatrixAddToolHandler())
add_tool_handler(MatrixMultiplyToolHandler())
add_tool_handler(MatrixSubtractToolHandler())
add_tool_handler(ElementWiseMultiplyToolHandler())
add_tool_handler(DotProductToolHandler())
add_tool_handler(MatrixTransposeToolHandler())
add_tool_handler(MatrixInverseToolHandler())
add_tool_handler(MatrixDeterminantToolHandler())
add_tool_handler(SolveLinearSystemToolHandler())
add_tool_handler(EigenDecompositionToolHandler())
add_tool_handler(SVDToolHandler())
add_tool_handler(QRDecompositionToolHandler())
add_tool_handler(MatrixPowerToolHandler())
add_tool_handler(FFTToolHandler())
add_tool_handler(PolynomialRootsToolHandler())
add_tool_handler(StatisticsToolHandler())
add_tool_handler(NumericalDerivativeToolHandler())
add_tool_handler(ConvolutionToolHandler())
add_tool_handler(RandomGeneratorToolHandler())

@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List all available NumPy tools"""
    return [th.get_tool_description() for th in tool_handlers.values()]

@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls for NumPy operations"""
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
            uri="numpy://operations",
            name="NumPy Operations",
            description="Available mathematical operations using NumPy",
            mimeType="text/plain"
        )
    ]

@app.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read resource content"""
    if uri == "numpy://operations":
        operations = [
            "Matrix Operations: Addition, Multiplication, Subtraction, Transpose, Inverse, Determinant, Power",
            "Linear Algebra: Solve linear systems, Eigenvalue decomposition, SVD, QR decomposition",
            "Signal Processing: Fast Fourier Transform, Convolution",
            "Statistics: Mean, Standard deviation, Variance, Min, Max, Median",
            "Calculus: Numerical derivatives",
            "Polynomial: Find roots of polynomials",
            "Random: Generate random numbers from various distributions"
        ]
        return "\n".join(operations)
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
