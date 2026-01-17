# Development Guide

## Getting Started with Development

### Setting Up Development Environment

1. **Fork and clone** the repository
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```
4. **Run tests**:
   ```bash
   pytest tests/
   ```

## Project Structure

```
ASWY_NexHacks/
├── backend/              # Python backend
│   ├── scanning/        # Camera and point cloud capture
│   ├── path_planning/   # Toolpath generation
│   ├── safety/          # Thermal safety
│   ├── visualization/   # Interactive visualization
│   ├── utils/           # Shared utilities
│   └── robot_control/   # Robot integration
├── frontend/            # React web UI
├── config/              # YAML configuration
├── data/                # Runtime data (gitignored)
├── docs/                # Documentation
├── tests/               # Test suites
└── run_*.py            # Entry point scripts
```

## Code Style

### Python

Follow **PEP 8** with these specifics:

- **Line length**: 100 characters max
- **Imports**: Group by stdlib, third-party, local
- **Docstrings**: Google style
- **Type hints**: Use when helpful

Example:

```python
from typing import List, Optional
import numpy as np

def generate_toolpath(
    surface: SurfaceModel,
    config: ToolpathConfig
) -> List[ToolpathPoint]:
    """
    Generate a raster toolpath over the surface.
    
    Args:
        surface: The surface model to generate path for
        config: Configuration parameters
        
    Returns:
        List of toolpath points
        
    Raises:
        ValueError: If surface is invalid
    """
    pass
```

### TypeScript/React

Follow **Airbnb Style Guide**:

- **Functional components** with hooks
- **TypeScript** for type safety
- **Props interfaces** for all components
- **Descriptive names**

Example:

```typescript
interface ModelViewerProps {
  modelUrl: string | null;
  isLoading: boolean;
  onError: (error: string) => void;
}

export const ModelViewer: React.FC<ModelViewerProps> = ({
  modelUrl,
  isLoading,
  onError
}) => {
  // Component logic
};
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific module
pytest tests/test_path_planning.py

# Run with coverage
pytest --cov=backend tests/

# Run frontend tests
cd frontend && npm test
```

### Writing Tests

#### Python Unit Tests

```python
import pytest
from backend.path_planning.surface_model import SurfaceModel

def test_surface_model_creation():
    """Test surface model initialization."""
    points = np.random.rand(1000, 3)
    surface = SurfaceModel(points, "test_surface")
    
    assert surface.surface_name == "test_surface"
    assert len(surface.points) == 1000

def test_surface_normal_calculation():
    """Test normal vector calculation."""
    # Create simple planar surface
    points = create_flat_surface()
    surface = SurfaceModel(points)
    
    normal = surface.get_normal(0, 0)
    
    # Should point upward for flat surface
    assert normal[1] > 0.9
```

#### Integration Tests

```python
def test_full_pipeline():
    """Test complete scan-plan-export pipeline."""
    # Load test point cloud
    pcd = load_test_pointcloud()
    
    # Create surface model
    surface = SurfaceModel(pcd, "test")
    
    # Generate toolpath
    config = ToolpathConfig()
    generator = RasterGenerator(surface, config)
    toolpath = generator.generate()
    
    # Export G-code
    filename = ResultsManager.export_gcode(toolpath)
    
    # Verify file exists
    assert os.path.exists(filename)
```

## Adding New Features

### Adding a New Path Planning Algorithm

1. **Create new file**: `backend/path_planning/spiral_generator.py`

```python
from typing import List
from .surface_model import SurfaceModel, ToolpathConfig, ToolpathPoint

class SpiralGenerator:
    """Generate spiral toolpath."""
    
    def __init__(self, surface: SurfaceModel, config: ToolpathConfig):
        self.surface = surface
        self.config = config
    
    def generate(self) -> List[ToolpathPoint]:
        """Generate spiral pattern."""
        # Implementation
        pass
```

2. **Add tests**: `tests/test_spiral_generator.py`

3. **Update docs**: Add to USAGE.md

4. **Create example**: Show how to use

### Adding a New Safety Check

1. **Extend ThermalSafetyAgent**:

```python
# backend/safety/thermal_predictor.py

def check_dwell_time(self, state: dict) -> bool:
    """Check if dwell time is safe."""
    dwell = state.get("dwell_time", 0)
    return dwell < self.max_dwell_time
```

2. **Update recommend_action()**:

```python
def recommend_action(self, state: dict):
    if not self.check_dwell_time(state):
        return {"action": "stop", "reason": "Dwell time exceeded"}
    # ... rest of checks
```

3. **Add configuration**: `config/safety_thresholds.yaml`

4. **Add tests**

### Adding a Wound Detection Module

1. **Create**: `backend/path_planning/wound_detector.py`

```python
import numpy as np
from sklearn.cluster import DBSCAN

class WoundDetector:
    """Detect wound regions in point clouds."""
    
    def detect(self, points: np.ndarray, colors: np.ndarray):
        """
        Detect wound region based on color analysis.
        
        Args:
            points: Nx3 point coordinates
            colors: Nx3 RGB colors
            
        Returns:
            Mask of wound region points
        """
        # Detect redness
        redness = colors[:, 0] / (colors[:, 1] + colors[:, 2] + 1e-6)
        
        # Threshold
        wound_mask = redness > 1.5
        
        # Cluster wound regions
        # ... implementation
        
        return wound_mask
```

2. **Integrate into pipeline**

3. **Add configuration parameters**

4. **Add tests and documentation**

## Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Surface model created with %d points", len(points))
```

### Visual Debugging

```python
import open3d as o3d

# Visualize point cloud
pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(points)
o3d.visualization.draw_geometries([pcd])
```

### Performance Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
generate_toolpath(surface, config)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(10)
```

## Git Workflow

### Branching Strategy

- `main`: Stable, production-ready
- `develop`: Integration branch
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Urgent production fixes

### Commit Messages

Follow **Conventional Commits**:

```
feat: add spiral path generator
fix: correct normal calculation for edge points
docs: update setup instructions
test: add integration test for full pipeline
refactor: extract G-code export to separate module
```

### Pull Request Process

1. **Create feature branch**
2. **Make changes** with tests
3. **Run tests** locally
4. **Update documentation**
5. **Create PR** with description
6. **Address review comments**
7. **Merge** when approved

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No new warnings
```

## Documentation

### Docstring Format

Use Google style:

```python
def calculate_standoff_surface(
    vertices: np.ndarray,
    normals: np.ndarray,
    distance: float
) -> np.ndarray:
    """
    Calculate offset surface at standoff distance.
    
    Offsets each vertex along its normal vector by the specified
    distance to create a standoff surface for plasma jet travel.
    
    Args:
        vertices: Nx3 array of surface vertices
        normals: Nx3 array of unit normal vectors
        distance: Standoff distance in millimeters
        
    Returns:
        Nx3 array of offset vertices
        
    Raises:
        ValueError: If vertices and normals have different shapes
        
    Example:
        >>> vertices = np.array([[0, 0, 0], [1, 0, 0]])
        >>> normals = np.array([[0, 1, 0], [0, 1, 0]])
        >>> offset = calculate_standoff_surface(vertices, normals, 5.0)
        >>> print(offset)
        [[0, 5, 0], [1, 5, 0]]
    """
    pass
```

### Updating Documentation

After significant changes:

1. Update relevant `.md` files in `docs/`
2. Update inline comments
3. Update docstrings
4. Add examples if needed

## Release Process

### Version Numbering

Follow **Semantic Versioning** (SemVer):

- `MAJOR.MINOR.PATCH`
- `1.0.0` → `1.0.1` (bugfix)
- `1.0.0` → `1.1.0` (new feature)
- `1.0.0` → `2.0.0` (breaking change)

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Version number bumped
- [ ] Git tag created
- [ ] Release notes written

## Common Development Tasks

### Add a New Configuration Parameter

1. Add to `config/*.yaml`
2. Update config class/dataclass
3. Use in code
4. Document in USAGE.md
5. Add test

### Add a New CLI Argument

```python
# run_planner.py

parser.add_argument(
    '--my-param',
    type=float,
    default=5.0,
    help='Description of parameter'
)
```

### Add a New Data Export Format

Extend `ResultsManager` in `backend/utils/file_io.py`:

```python
@staticmethod
def export_xml(toolpath, filename=None):
    """Export toolpath to XML format."""
    # Implementation
    pass
```

## Useful Resources

- **Python**: https://docs.python.org/3/
- **NumPy**: https://numpy.org/doc/
- **Open3D**: http://www.open3d.org/docs/
- **RealSense**: https://github.com/IntelRealSense/librealsense
- **React**: https://react.dev/
- **Three.js**: https://threejs.org/docs/

## Getting Help

- Check existing issues and discussions
- Read the documentation thoroughly
- Ask in team chat
- Create a detailed issue with:
  - What you tried
  - What you expected
  - What actually happened
  - Minimal reproducible example

## Contributing

We welcome contributions! See the process above for how to submit changes.

Key areas for contribution:
- Wound detection algorithms
- Additional path planning patterns
- Robot arm integrations
- Performance optimizations
- Documentation improvements
- Test coverage

