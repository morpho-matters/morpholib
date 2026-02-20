import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Any

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """Provide a sample configuration dictionary for tests."""
    return {
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "background_color": [0, 0, 0],
        "antialiasing": True,
        "export_format": "mp4"
    }


@pytest.fixture
def mock_cairo_context(mocker):
    """Mock cairo context for graphics tests."""
    mock_ctx = mocker.Mock()
    mock_ctx.move_to = mocker.Mock()
    mock_ctx.line_to = mocker.Mock()
    mock_ctx.stroke = mocker.Mock()
    mock_ctx.fill = mocker.Mock()
    mock_ctx.set_source_rgb = mocker.Mock()
    mock_ctx.set_source_rgba = mocker.Mock()
    mock_ctx.save = mocker.Mock()
    mock_ctx.restore = mocker.Mock()
    mock_ctx.translate = mocker.Mock()
    mock_ctx.scale = mocker.Mock()
    mock_ctx.rotate = mocker.Mock()
    return mock_ctx


@pytest.fixture
def mock_surface(mocker):
    """Mock cairo surface for graphics tests."""
    mock_surface = mocker.Mock()
    mock_surface.write_to_png = mocker.Mock()
    mock_surface.get_width = mocker.Mock(return_value=1920)
    mock_surface.get_height = mocker.Mock(return_value=1080)
    return mock_surface


@pytest.fixture
def sample_animation_data() -> dict[str, Any]:
    """Provide sample animation data for tests."""
    return {
        "frames": [
            {"time": 0.0, "objects": []},
            {"time": 0.033, "objects": []},
            {"time": 0.066, "objects": []}
        ],
        "duration": 3.0,
        "fps": 30,
        "name": "test_animation"
    }


@pytest.fixture
def sample_figure_data() -> dict[str, Any]:
    """Provide sample figure data for tests."""
    return {
        "vertices": [(0, 0), (1, 0), (1, 1), (0, 1)],
        "edges": [(0, 1), (1, 2), (2, 3), (3, 0)],
        "color": [1.0, 0.0, 0.0],
        "fill": True,
        "stroke_width": 2.0
    }


@pytest.fixture
def cleanup_files(temp_dir: Path) -> Generator[list[Path], None, None]:
    """Track and cleanup files created during tests."""
    files_to_cleanup = []
    
    yield files_to_cleanup
    
    for file_path in files_to_cleanup:
        if file_path.exists():
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)


@pytest.fixture(autouse=True)
def reset_morpholib_state():
    """Reset any global state in morpholib between tests."""
    yield
    

@pytest.fixture
def mock_ffmpeg(mocker):
    """Mock FFmpeg subprocess calls for video export tests."""
    mock_popen = mocker.patch('subprocess.Popen')
    mock_process = mocker.Mock()
    mock_process.stdin = mocker.Mock()
    mock_process.wait = mocker.Mock(return_value=0)
    mock_process.communicate = mocker.Mock(return_value=(b'', b''))
    mock_popen.return_value = mock_process
    return mock_process


@pytest.fixture
def isolated_morpholib_import(monkeypatch):
    """Provide isolated morpholib import to avoid side effects."""
    modules_backup = sys.modules.copy()
    
    morpholib_modules = [key for key in sys.modules.keys() if key.startswith('morpholib')]
    for module in morpholib_modules:
        del sys.modules[module]
    
    yield
    
    sys.modules.clear()
    sys.modules.update(modules_backup)