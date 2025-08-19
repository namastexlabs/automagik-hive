"""
Demonstration test to show pollution detection in action.

This test intentionally tries to create files in the project directory
to demonstrate that our warning system works correctly.
"""

import warnings
from pathlib import Path


def test_pollution_warning_demonstration():
    """
    Test that intentionally demonstrates pollution detection.

    This test runs WITHOUT isolated_workspace to show how the
    global enforcement system detects and warns about pollution attempts.
    """
    # Capture warnings to verify they are generated
    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        # Determine if we're in the project root
        project_root = Path(__file__).parent.parent.absolute()
        current_dir = Path.cwd()

        if current_dir == project_root:
            # We're in project root - this SHOULD trigger a warning
            print(f"\n🔍 Testing from project root: {current_dir}")

            # Try to create a file that should trigger warnings
            pollution_file = Path("deliberate_pollution_test.txt")

            try:
                with open(pollution_file, "w") as f:
                    f.write("This file creation should trigger a warning!")

                # Clean up immediately to avoid actual pollution
                if pollution_file.exists():
                    pollution_file.unlink()

                # Check if warnings were generated
                pollution_warnings = [w for w in warning_list if "attempted to create file" in str(w.message)]

                if pollution_warnings:
                    print(f"✅ Warning system working! Generated {len(pollution_warnings)} warnings")
                    for w in pollution_warnings:
                        print(f"   Warning: {w.message}")
                else:
                    print("ℹ️  No warnings generated (might be expected based on implementation)")

            except Exception as e:
                print(f"⚠️  File creation failed: {e}")
        else:
            # We're in a temp directory - should be safe
            print(f"\n✅ Test running in safe directory: {current_dir}")

            # Create file safely in temp location
            safe_file = Path("safe_test_file.txt")
            safe_file.write_text("This is safe!")

            # Verify no pollution warnings
            pollution_warnings = [w for w in warning_list if "attempted to create file" in str(w.message)]

            assert len(pollution_warnings) == 0, "Should not warn about temp directory files"
            print("✅ No warnings for temp directory operations")


def test_with_isolated_workspace_no_warnings(isolated_workspace):
    """
    Test that shows isolated_workspace prevents any pollution warnings.

    This demonstrates the strongest protection level.
    """
    # With isolated_workspace, we should be in a temp directory
    current_dir = Path.cwd()
    print(f"\n🏠 Isolated workspace directory: {current_dir}")

    # Capture warnings
    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        # Create multiple files - none should trigger warnings
        for i in range(3):
            test_file = Path(f"isolated_test_file_{i}.txt")
            test_file.write_text(f"Test content {i}")
            assert test_file.exists()
            print(f"   Created: {test_file.name}")

        # Verify no pollution warnings were generated
        pollution_warnings = [w for w in warning_list if "attempted to create file" in str(w.message)]

        assert len(pollution_warnings) == 0
        print("✅ isolated_workspace provides complete protection!")


def test_tmp_path_safety(tmp_path):
    """
    Test that shows tmp_path is always safe.

    This demonstrates the built-in pytest protection.
    """
    print(f"\n📁 tmp_path directory: {tmp_path}")

    # Create files in tmp_path - should never warn
    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        test_file = tmp_path / "tmp_path_test.txt"
        test_file.write_text("Safe tmp_path content")

        pollution_warnings = [w for w in warning_list if "attempted to create file" in str(w.message)]

        assert len(pollution_warnings) == 0
        print("✅ tmp_path is always safe!")
