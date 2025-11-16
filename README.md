# Blender Camera

A FastAPI-based REST API server for managing Blender scenes and rendering camera views with depth, normal, and color outputs.

## Overview

`blender-camera` provides a REST API for interacting with Blender scenes programmatically. Upload `.blend` files, create and manage cameras, and render frames with depth maps, surface normals, and RGB color data. The service runs Blender in headless mode to generate renders and export point clouds.

## Features

- **Scene Management**: Upload and manage multiple Blender scenes
- **Camera Control**: Create cameras and control their pose (position and rotation)
- **Frame Rendering**: Render frames from camera perspectives with:
  - RGB color images (PNG)
  - Depth maps (PNG)
  - Surface normals (PNG)
  - Point clouds (PLY format)
- **Camera Intrinsics**: Configure camera parameters (focal length, principal point)
- **Entity Management**: Manage scene entities with poses and camera properties

## Requirements

- Python >= 3.12
- Blender (for rendering)
- Docker (optional, for containerized deployment)

## Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/ardo314/blender-camera.git
cd blender-camera
```

2. Install dependencies using `uv`:
```bash
pip install uv
uv sync
```

3. Ensure Blender is installed and available in your system PATH.

### Docker Deployment

Build and run using Docker:
```bash
docker build -t blender-camera .
docker run -p 8080:8080 blender-camera
```

## Usage

### Starting the Server

Run the server locally:
```bash
uv run serve
```

The API will be available at `http://localhost:8080`.

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

### API Endpoints

#### Scenes

- `POST /scenes` - Upload a new Blender scene (`.blend` file)
- `GET /scenes` - List all scenes
- `DELETE /scenes/{scene_id}` - Delete a scene

#### Cameras

- `POST /scenes/{scene_id}/cameras` - Create a new camera in the scene

#### Entities

- `GET /scenes/{scene_id}/entities` - List all entities in a scene
- `POST /scenes/{scene_id}/entities` - Create a new entity
- `GET /scenes/{scene_id}/entities/{entity_id}` - Get entity details
- `DELETE /scenes/{scene_id}/entities/{entity_id}` - Delete an entity
- `GET /scenes/{scene_id}/entities/{entity_id}/pose` - Get entity pose
- `PUT /scenes/{scene_id}/entities/{entity_id}/pose` - Update entity pose
- `GET /scenes/{scene_id}/entities/{entity_id}/camera-intrinsics` - Get camera intrinsics
- `PUT /scenes/{scene_id}/entities/{entity_id}/camera-intrinsics` - Update camera intrinsics

#### Rendering

- `GET /scenes/{scene_id}/entities/{entity_id}/colors` - Render RGB color image (PNG)
- `GET /scenes/{scene_id}/entities/{entity_id}/depth` - Render depth map (PNG)
- `GET /scenes/{scene_id}/entities/{entity_id}/normals` - Render surface normals (PNG)
- `GET /scenes/{scene_id}/entities/{entity_id}/pointcloud` - Export point cloud (PLY)

### Example Workflow

1. **Upload a scene**:
```bash
curl -X POST http://localhost:8080/scenes \
  -F "file=@scene.blend"
```

2. **Create a camera**:
```bash
curl -X POST http://localhost:8080/scenes/{scene_id}/cameras
```

3. **Update camera pose**:
```bash
curl -X PUT http://localhost:8080/scenes/{scene_id}/entities/{camera_id}/pose \
  -H "Content-Type: application/json" \
  -d '[0, 0, 5, 0, 0, 0]'
```

4. **Render a color image**:
```bash
curl http://localhost:8080/scenes/{scene_id}/entities/{camera_id}/colors \
  -o output.png
```

## Project Structure

```
src/blender_camera/
├── api/              # FastAPI routes and routers
├── models/           # Data models (Scene, Camera, Entity, Frame, Pose)
├── scripts/          # Blender rendering scripts
├── app.py            # Application setup
├── blender.py        # Blender process manager
└── utils.py          # Utility functions

tests/
├── integration/      # Integration tests
└── unit/            # Unit tests
```

## Development

### Running Tests

```bash
uv run pytest
```

### Code Quality

The project uses:
- **Ruff** for linting and formatting
- **MyPy** for type checking

Run checks:
```bash
uv run ruff check
uv run mypy src
```

## Dependencies

- **FastAPI** - Web framework
- **Blender** - 3D rendering engine
- **Open3D** - Point cloud processing
- **Pillow** - Image processing
- **OpenEXR** - HDR image format support
- **NumPy** - Numerical computing
