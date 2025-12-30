"""
Test Coverage Detector
Detects if source files have corresponding test files
"""
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class TestCoverageDetector:
    """Detects test coverage by finding test files"""
    
    # Test file patterns
    TEST_PATTERNS = [
        'test_',      # test_module.py
        '_test.',     # module_test.js
        '.test.',     # module.test.ts
        'spec_',      # spec_module.py
        '_spec.',     # module_spec.js
        '.spec.'      # module.spec.ts
    ]
    
    # Test directories
    TEST_DIRS = [
        'test',
        'tests',
        '__test__',
        '__tests__',
        'spec',
        'specs'
    ]
    
    def detect_test_coverage(
        self,
        scan_dir: Path,
        source_files: List[str]
    ) -> Dict[str, bool]:
        """
        Detect which source files have test coverage.
        
        Args:
            scan_dir: Repository root directory
            source_files: List of source file paths (relative)
            
        Returns:
            Dict mapping source_file_path -> has_test (bool)
        """
        coverage_map = {}
        
        # Find all test files
        test_files = self._find_test_files(scan_dir)
        logger.info(f"Found {len(test_files)} test files")
        
        for source_file in source_files:
            coverage_map[source_file] = self._has_corresponding_test(
                source_file,
                test_files
            )
        
        covered = sum(1 for has_test in coverage_map.values() if has_test)
        logger.info(f"Test coverage: {covered}/{len(source_files)} files ({int(covered/len(source_files)*100) if source_files else 0}%)")
        
        return coverage_map
    
    def _find_test_files(self, scan_dir: Path) -> List[str]:
        """Find all test files in repository"""
        test_files = []
        
        for root, dirs, files in scan_dir.walk() if hasattr(scan_dir, 'walk') else [(scan_dir, [], [])]:
            # Check if in test directory
            root_lower = str(root).lower()
            is_test_dir = any(test_dir in root_lower for test_dir in self.TEST_DIRS)
            
            for file in files:
                file_lower = file.lower()
                
                # Check test patterns
                is_test_file = any(pattern in file_lower for pattern in self.TEST_PATTERNS)
                
                if is_test_dir or is_test_file:
                    rel_path = str(Path(root) / file)
                    test_files.append(rel_path)
        
        return test_files
    
    def _has_corresponding_test(
        self,
        source_file: str,
        test_files: List[str]
    ) -> bool:
        """Check if source file has a corresponding test file"""
        
        # Extract base name without extension
        source_path = Path(source_file)
        source_stem = source_path.stem  # filename without extension
        
        # Common test naming patterns
        possible_test_names = [
            f"test_{source_stem}",       # test_module.py
            f"{source_stem}_test",       # module_test.js
            f"{source_stem}.test",       # module.test.ts
            f"test{source_stem}",        # testModule.java
            f"{source_stem}Test",        # ModuleTest.java
            f"{source_stem}_spec",       # module_spec.js
            f"{source_stem}.spec"        # module.spec.ts
        ]
        
        # Check if any test file matches
        for test_file in test_files:
            test_stem = Path(test_file).stem
            
            if test_stem in possible_test_names:
                return True
            
            # Also check if source name is in test name (loose matching)
            if source_stem.lower() in test_stem.lower():
                return True
        
        return False
