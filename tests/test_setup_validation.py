import sys
import os
import pytest
from pathlib import Path


class TestSetupValidation:
    """Validation tests to ensure the testing infrastructure is properly configured."""
    
    def test_morpholib_importable(self):
        """Test that morpholib can be imported."""
        try:
            import morpholib
            assert morpholib is not None
            assert hasattr(morpholib, '__version__') or hasattr(morpholib, '__name__')
        except ImportError as e:
            # Skip test if optional dependencies are missing
            missing_deps = ["numpy", "pyglet", "PIL"]
            if any(dep in str(e) for dep in missing_deps):
                pytest.skip(f"Optional dependency not installed: {e}")
            else:
                raise
    
    def test_testing_directory_structure(self):
        """Verify the testing directory structure exists."""
        test_root = Path(__file__).parent
        assert test_root.exists()
        assert test_root.name == "tests"
        
        assert (test_root / "__init__.py").exists()
        assert (test_root / "conftest.py").exists()
        assert (test_root / "unit").exists()
        assert (test_root / "unit" / "__init__.py").exists()
        assert (test_root / "integration").exists()
        assert (test_root / "integration" / "__init__.py").exists()
    
    def test_pytest_configuration(self):
        """Verify pytest is properly configured."""
        import pytest
        
        # Simply verify pytest is installed and can be imported
        assert pytest is not None
        assert hasattr(pytest, 'mark')
        assert hasattr(pytest, 'fixture')
    
    def test_fixtures_available(self, temp_dir, sample_config):
        """Test that custom fixtures are available and working."""
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        
        assert isinstance(sample_config, dict)
        assert "width" in sample_config
        assert "height" in sample_config
        assert "fps" in sample_config
    
    @pytest.mark.unit
    def test_unit_marker(self):
        """Test that unit test marker works."""
        assert True
    
    @pytest.mark.integration
    def test_integration_marker(self):
        """Test that integration test marker works."""
        assert True
    
    @pytest.mark.slow
    def test_slow_marker(self):
        """Test that slow test marker works."""
        assert True
    
    def test_mock_fixtures(self, mock_cairo_context, mock_surface):
        """Test that mocking fixtures work properly."""
        mock_cairo_context.move_to(0, 0)
        mock_cairo_context.line_to(100, 100)
        
        assert mock_cairo_context.move_to.called
        assert mock_cairo_context.line_to.called
        assert mock_cairo_context.line_to.call_args[0] == (100, 100)
        
        assert mock_surface.get_width() == 1920
        assert mock_surface.get_height() == 1080
    
    def test_coverage_import(self):
        """Test that coverage tools are available."""
        try:
            import coverage
            assert coverage is not None
        except ImportError:
            pytest.skip("Coverage not installed yet")
    
    def test_project_root_in_path(self):
        """Verify project root is in Python path for imports."""
        project_root = Path(__file__).parent.parent
        assert str(project_root) in sys.path or str(project_root.absolute()) in sys.path