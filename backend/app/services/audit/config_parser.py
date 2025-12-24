import yaml
from typing import Dict, Any, Optional
from pathlib import Path
import logging
import copy

logger = logging.getLogger(__name__)

# Default configuration - V1 behavior
DEFAULT_CONFIG = {
    "version": "1.0",
    "rules": {
        "hotspot": {
            "enabled": True,
            "thresholds": {"complexity": 25, "churn": 10},
            "severity": "critical"
        },
        "deep_nesting": {
            "enabled": True,
            "thresholds": {"indent_depth": 6},
            "severity": "high"
        },
        "large_file": {
            "enabled": True,
            "thresholds": {"loc": 300},
            "severity": "medium"
        },
        "complex_module": {
            "enabled": True,
            "thresholds": {"complexity": 35},
            "severity": "high"
        },
        "no_tests": {
            "enabled": True,
            "thresholds": {"min_loc": 100},
            "severity": "medium"
        }
    },
    "settings": {
        "pr_comments": {
            "enabled": True,
            "severity_filter": "critical_high"
        }
    }
}

class RevFloConfig:
    """
    Parser and validator for .revflo.yml configuration files.
    V2 Feature: Rule Configuration
    """
    
    VALID_SEVERITIES = ["critical", "high", "medium", "low"]
    CONFIG_FILENAMES = [".revflo.yml", ".revflo.yaml", ".github/revflo.yml"]
    
    def __init__(self, config_dict: Dict[str, Any] = None):
        """Initialize with custom config or defaults."""
        self.config = self._merge_with_defaults(config_dict or {})
        self._validate()
        logger.info(f"RevFlowConfig initialized with {len(self.config['rules'])} rules")
    
    @classmethod
    def from_file(cls, repo_path: Path) -> "RevFloConfig":
        """
        Load configuration from repository.
        Searches for config files in order:
        1. .revflo.yml
        2. .revflo.yaml
        3. .github/revflo.yml
        
        Returns default config if no file found.
        """
        for filename in cls.CONFIG_FILENAMES:
            config_path = repo_path / filename
            if config_path.exists():
                logger.info(f"Found config file: {config_path}")
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_dict = yaml.safe_load(f) or {}
                    
                    # Validate it's a dict
                    if not isinstance(config_dict, dict):
                        raise ValueError("Configuration file must contain a YAML dictionary")
                    
                    return cls(config_dict)
                    
                except yaml.YAMLError as e:
                    logger.error(f"Invalid YAML in {config_path}: {e}")
                    raise ValueError(f"Invalid YAML syntax in configuration file: {e}")
                except Exception as e:
                    logger.error(f"Error loading config from {config_path}: {e}")
                    raise ValueError(f"Failed to load configuration file: {e}")
        
        logger.info("No config file found, using defaults")
        return cls()
    
    def _merge_with_defaults(self, user_config: Dict) -> Dict:
        """
        Merge user config with defaults.
        User values override defaults, but missing keys use defaults.
        """
        config = copy.deepcopy(DEFAULT_CONFIG)
        
        # Merge rules
        if "rules" in user_config:
            for rule_name, rule_config in user_config["rules"].items():
                if rule_name in config["rules"]:
                    # Merge this rule's config
                    config["rules"][rule_name].update(rule_config)
                    
                    # Deep merge thresholds
                    if "thresholds" in rule_config:
                        config["rules"][rule_name]["thresholds"].update(
                            rule_config["thresholds"]
                        )
        
        # Merge settings
        if "settings" in user_config:
            if "pr_comments" in user_config["settings"]:
                config["settings"]["pr_comments"].update(
                    user_config["settings"]["pr_comments"]
                )
        
        return config
    
    def _validate(self):
        """Validate configuration values."""
        # Validate rules
        for rule_name, rule_config in self.config["rules"].items():
            # Validate severity
            severity = rule_config.get("severity")
            if severity not in self.VALID_SEVERITIES:
                raise ValueError(
                    f"Invalid severity '{severity}' for rule '{rule_name}'. "
                    f"Must be one of: {', '.join(self.VALID_SEVERITIES)}"
                )
            
            # Validate enabled is boolean
            enabled = rule_config.get("enabled")
            if not isinstance(enabled, bool):
                raise ValueError(
                    f"Invalid 'enabled' value for rule '{rule_name}'. Must be true or false."
                )
            
            # Validate thresholds are positive numbers
            thresholds = rule_config.get("thresholds", {})
            for threshold_name, threshold_value in thresholds.items():
                if not isinstance(threshold_value, (int, float)):
                    raise ValueError(
                        f"Invalid threshold '{threshold_name}' for rule '{rule_name}'. "
                        f"Must be a number."
                    )
                if threshold_value < 0:
                    raise ValueError(
                        f"Invalid threshold '{threshold_name}' for rule '{rule_name}'. "
                        f"Must be positive (got {threshold_value})."
                    )
        
        # Validate PR comment settings
        pr_settings = self.config["settings"]["pr_comments"]
        if not isinstance(pr_settings.get("enabled"), bool):
            raise ValueError("settings.pr_comments.enabled must be true or false")
        
        severity_filter = pr_settings.get("severity_filter")
        valid_filters = ["all", "critical_high", "critical"]
        if severity_filter not in valid_filters:
            raise ValueError(
                f"Invalid severity_filter '{severity_filter}'. "
                f"Must be one of: {', '.join(valid_filters)}"
            )
    
    def get_rule_config(self, rule_name: str) -> Dict[str, Any]:
        """Get configuration for a specific rule."""
        return self.config["rules"].get(rule_name, {})
    
    def is_rule_enabled(self, rule_name: str) -> bool:
        """Check if a rule is enabled."""
        return self.get_rule_config(rule_name).get("enabled", False)
    
    def get_threshold(self, rule_name: str, threshold_name: str) -> float:
        """Get threshold value for a rule."""
        thresholds = self.get_rule_config(rule_name).get("thresholds", {})
        return thresholds.get(threshold_name, 0)
    
    def get_severity(self, rule_name: str) -> str:
        """Get severity for a rule."""
        return self.get_rule_config(rule_name).get("severity", "medium")
    
    def get_pr_comment_settings(self) -> Dict[str, Any]:
        """Get PR comment configuration."""
        return self.config["settings"]["pr_comments"]
    
    def get_enabled_rules_count(self) -> int:
        """Get count of enabled rules."""
        return sum(1 for rule in self.config["rules"].values() if rule["enabled"])
