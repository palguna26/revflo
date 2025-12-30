"""
Metric Computer - Shared utility for V2 and V3
Calculates file-level metrics (complexity, LOC, etc.)
"""
import logging
from pathlib import Path
from typing import List, Dict, Optional
from radon.complexity import cc_visit

logger = logging.getLogger(__name__)


class MetricComputer:
    """
    Computes file-level metrics.
    
    Shared by:
    - V2 scanner (scanner.py)
    - V3 dimension scanners
    """
    
    @staticmethod
    def calculate_loc(lines: List[str]) -> int:
        """Calculate lines of code (non-empty, non-comment)"""
        return len([l for l in lines if l.strip() and not l.strip().startswith('#')])
    
    @staticmethod
    def calculate_indent_depth(lines: List[str]) -> int:
        """Calculate maximum indentation depth"""
        max_depth = 0
        for line in lines:
            if line.strip():
                stripped = line.lstrip()
                indent = len(line) - len(stripped)
                spaces = indent // 4  # Assuming 4-space indents
                max_depth = max(max_depth, spaces)
        return max_depth
    
    @staticmethod
    def calculate_complexity(content: str, file_path: str) -> int:
        """
        Calculate cyclomatic complexity.
        
        - Python: Uses Radon for real complexity
        - Other languages: Uses proxy heuristic
        """
        lines = content.splitlines()
        
        # Real complexity for Python
        if file_path.endswith('.py'):
            try:
                complexity_results = cc_visit(content)
                # Sum complexity of all functions/methods
                return sum(item.complexity for item in complexity_results)
            except Exception as e:
                logger.warning(f"Radon failed for {file_path}, using proxy: {e}")
                return MetricComputer._proxy_complexity(lines)
        else:
            # Proxy for other languages
            return MetricComputer._proxy_complexity(lines)
    
    @staticmethod
    def _proxy_complexity(lines: List[str]) -> int:
        """
        Proxy complexity heuristic for non-Python files.
        Counts deep nesting and long lines.
        """
        score = 0
        for line in lines:
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            if indent >= 8:
                score += 1  # Deep nesting
            if len(line) > 120:
                score += 0.5  # Long lines
        return int(score)
    
    @staticmethod
    def analyze_file(file_path: Path, rel_path: str) -> Optional[Dict]:
        """
        Analyze a single file and return metrics.
        
        Returns dict with: complexity, loc, indent_depth, language
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
            
            # Determine language
            lang = "unknown"
            if rel_path.endswith('.py'):
                lang = "python"
            elif rel_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                lang = "javascript"
            elif rel_path.endswith('.java'):
                lang = "java"
            elif rel_path.endswith(('.cpp', '.cc', '.cxx')):
                lang = "cpp"
            
            return {
                'complexity': MetricComputer.calculate_complexity(content, rel_path),
                'loc': MetricComputer.calculate_loc(lines),
                'indent_depth': MetricComputer.calculate_indent_depth(lines),
                'language': lang
            }
        except Exception as e:
            logger.warning(f"Failed to analyze {rel_path}: {e}")
            return None
