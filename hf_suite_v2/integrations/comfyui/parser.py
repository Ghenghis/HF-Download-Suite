"""
ComfyUI workflow parser - Extract model references from workflow JSON.

Supports:
- Standard workflow.json format
- API workflow format
- Embedded workflows in PNG metadata
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ModelReference:
    """A reference to a model in a ComfyUI workflow."""
    
    name: str
    model_type: str  # checkpoint, lora, vae, controlnet, embedding, upscaler, clip
    node_type: str
    node_id: str
    file_path: Optional[str] = None
    repo_id: Optional[str] = None  # If resolvable to HF repo
    required: bool = True
    
    @property
    def display_name(self) -> str:
        return self.name.replace("\\", "/").split("/")[-1]


@dataclass
class WorkflowInfo:
    """Parsed workflow information."""
    
    source_file: Optional[str] = None
    format_version: Optional[str] = None
    node_count: int = 0
    models: List[ModelReference] = field(default_factory=list)
    missing_models: List[ModelReference] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @property
    def checkpoint_models(self) -> List[ModelReference]:
        return [m for m in self.models if m.model_type == "checkpoint"]
    
    @property
    def lora_models(self) -> List[ModelReference]:
        return [m for m in self.models if m.model_type == "lora"]
    
    @property
    def vae_models(self) -> List[ModelReference]:
        return [m for m in self.models if m.model_type == "vae"]


class ComfyUIWorkflowParser:
    """
    Parser for ComfyUI workflow files.
    
    Extracts model references from workflow JSON and identifies
    which models need to be downloaded.
    
    Usage:
        parser = ComfyUIWorkflowParser()
        info = parser.parse_file("workflow.json")
        
        for model in info.models:
            print(f"{model.model_type}: {model.name}")
    """
    
    # Node types that reference models
    MODEL_NODE_TYPES = {
        # Checkpoints
        "CheckpointLoaderSimple": {"input": "ckpt_name", "type": "checkpoint"},
        "CheckpointLoader": {"input": "ckpt_name", "type": "checkpoint"},
        "UNETLoader": {"input": "unet_name", "type": "checkpoint"},
        "DualCLIPLoader": {"input": ["clip_name1", "clip_name2"], "type": "clip"},
        
        # LoRA
        "LoraLoader": {"input": "lora_name", "type": "lora"},
        "LoraLoaderModelOnly": {"input": "lora_name", "type": "lora"},
        
        # VAE
        "VAELoader": {"input": "vae_name", "type": "vae"},
        
        # ControlNet
        "ControlNetLoader": {"input": "control_net_name", "type": "controlnet"},
        "DiffControlNetLoader": {"input": "control_net_name", "type": "controlnet"},
        
        # Upscalers
        "UpscaleModelLoader": {"input": "model_name", "type": "upscaler"},
        
        # CLIP
        "CLIPLoader": {"input": "clip_name", "type": "clip"},
        "CLIPVisionLoader": {"input": "clip_name", "type": "clip"},
        
        # Embeddings (handled via text)
        "CLIPTextEncode": {"input": "text", "type": "embedding", "pattern": r"embedding:([^\s,]+)"},
        
        # Style models
        "StyleModelLoader": {"input": "style_model_name", "type": "style"},
        
        # GLIGEN
        "GLIGENLoader": {"input": "gligen_name", "type": "gligen"},
        
        # IPAdapter
        "IPAdapterModelLoader": {"input": "ipadapter_file", "type": "ipadapter"},
        
        # Efficient loader (from efficiency nodes)
        "Efficient Loader": {"input": "ckpt_name", "type": "checkpoint"},
    }
    
    def __init__(self, comfy_root: Optional[str] = None):
        """
        Initialize parser.
        
        Args:
            comfy_root: Path to ComfyUI installation (for model path resolution)
        """
        self.comfy_root = Path(comfy_root) if comfy_root else None
    
    def parse_file(self, filepath: str) -> WorkflowInfo:
        """
        Parse a workflow file.
        
        Args:
            filepath: Path to workflow JSON or PNG with embedded workflow
            
        Returns:
            WorkflowInfo with extracted model references
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            return WorkflowInfo(errors=[f"File not found: {filepath}"])
        
        try:
            if filepath.suffix.lower() == ".png":
                workflow_data = self._extract_from_png(filepath)
            else:
                with open(filepath, "r", encoding="utf-8") as f:
                    workflow_data = json.load(f)
            
            return self.parse_workflow(workflow_data, str(filepath))
            
        except json.JSONDecodeError as e:
            return WorkflowInfo(errors=[f"Invalid JSON: {e}"])
        except Exception as e:
            return WorkflowInfo(errors=[f"Parse error: {e}"])
    
    def parse_workflow(self, workflow: Dict, source: str = None) -> WorkflowInfo:
        """
        Parse workflow data dictionary.
        
        Args:
            workflow: Workflow dictionary (nodes format or API format)
            source: Optional source file path
            
        Returns:
            WorkflowInfo with extracted model references
        """
        info = WorkflowInfo(source_file=source)
        
        try:
            # Detect format and get nodes
            if "nodes" in workflow:
                # Standard workflow format with nodes array
                nodes = self._convert_nodes_format(workflow["nodes"])
                info.format_version = "nodes_array"
            elif isinstance(workflow, dict) and all(k.isdigit() or k.startswith("_") for k in workflow.keys() if k not in ["last_node_id", "last_link_id", "version"]):
                # API format with numbered node keys
                nodes = workflow
                info.format_version = "api"
            else:
                # Try to find nodes in nested structure
                nodes = workflow
                info.format_version = "unknown"
            
            info.node_count = len(nodes)
            
            # Extract model references
            for node_id, node_data in nodes.items():
                if not isinstance(node_data, dict):
                    continue
                
                models = self._extract_models_from_node(node_id, node_data)
                info.models.extend(models)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_models = []
            for model in info.models:
                key = (model.name, model.model_type)
                if key not in seen:
                    seen.add(key)
                    unique_models.append(model)
            info.models = unique_models
            
            # Check which models are missing (if comfy_root is set)
            if self.comfy_root:
                info.missing_models = self._find_missing_models(info.models)
            
        except Exception as e:
            info.errors.append(f"Parse error: {e}")
            logger.exception("Workflow parse error")
        
        return info
    
    def _convert_nodes_format(self, nodes_array: List[Dict]) -> Dict:
        """Convert nodes array format to dict format."""
        nodes_dict = {}
        for node in nodes_array:
            node_id = str(node.get("id", len(nodes_dict)))
            nodes_dict[node_id] = {
                "class_type": node.get("type"),
                "inputs": self._extract_widget_values(node),
            }
        return nodes_dict
    
    def _extract_widget_values(self, node: Dict) -> Dict:
        """Extract widget values from node."""
        inputs = {}
        
        # Get from widgets_values
        widget_values = node.get("widgets_values", [])
        widget_order = node.get("widgets_order", [])
        
        # Map values to input names if possible
        if widget_order and len(widget_values) == len(widget_order):
            for i, name in enumerate(widget_order):
                inputs[name] = widget_values[i]
        else:
            # Fallback: use positional
            for i, val in enumerate(widget_values):
                inputs[f"widget_{i}"] = val
        
        # Also check 'inputs' if present
        if "inputs" in node:
            for inp in node.get("inputs", []):
                if isinstance(inp, dict):
                    name = inp.get("name")
                    if name and "widget" in inp:
                        inputs[name] = inp.get("widget", {}).get("value")
        
        return inputs
    
    def _extract_models_from_node(self, node_id: str, node_data: Dict) -> List[ModelReference]:
        """Extract model references from a single node."""
        models = []
        
        class_type = node_data.get("class_type", "")
        inputs = node_data.get("inputs", {})
        
        # Check if this is a model loader node
        node_config = self.MODEL_NODE_TYPES.get(class_type)
        
        if node_config:
            input_keys = node_config["input"]
            model_type = node_config["type"]
            
            if isinstance(input_keys, str):
                input_keys = [input_keys]
            
            for input_key in input_keys:
                value = inputs.get(input_key)
                
                if value and isinstance(value, str):
                    # Check for pattern (e.g., embeddings in text)
                    if "pattern" in node_config:
                        pattern = node_config["pattern"]
                        matches = re.findall(pattern, value)
                        for match in matches:
                            models.append(ModelReference(
                                name=match,
                                model_type=model_type,
                                node_type=class_type,
                                node_id=node_id,
                            ))
                    else:
                        # Direct model reference
                        models.append(ModelReference(
                            name=value,
                            model_type=model_type,
                            node_type=class_type,
                            node_id=node_id,
                        ))
        
        return models
    
    def _extract_from_png(self, filepath: Path) -> Dict:
        """Extract workflow from PNG metadata."""
        try:
            from PIL import Image
            
            img = Image.open(filepath)
            
            # Check for workflow in PNG metadata
            if hasattr(img, "text"):
                if "workflow" in img.text:
                    return json.loads(img.text["workflow"])
                if "prompt" in img.text:
                    return json.loads(img.text["prompt"])
            
            # Check EXIF
            if hasattr(img, "_getexif") and img._getexif():
                exif = img._getexif()
                # UserComment field (0x9286)
                if 0x9286 in exif:
                    data = exif[0x9286]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8", errors="ignore")
                    if data.startswith("{"):
                        return json.loads(data)
            
        except ImportError:
            logger.warning("PIL not available for PNG workflow extraction")
        except Exception as e:
            logger.warning(f"Failed to extract workflow from PNG: {e}")
        
        return {}
    
    def _find_missing_models(self, models: List[ModelReference]) -> List[ModelReference]:
        """Find models that don't exist locally."""
        missing = []
        
        if not self.comfy_root:
            return missing
        
        model_dirs = {
            "checkpoint": self.comfy_root / "models" / "checkpoints",
            "lora": self.comfy_root / "models" / "loras",
            "vae": self.comfy_root / "models" / "vae",
            "controlnet": self.comfy_root / "models" / "controlnet",
            "upscaler": self.comfy_root / "models" / "upscale_models",
            "clip": self.comfy_root / "models" / "clip",
            "embedding": self.comfy_root / "models" / "embeddings",
        }
        
        for model in models:
            model_dir = model_dirs.get(model.model_type)
            if not model_dir:
                continue
            
            # Check if model file exists
            model_path = model_dir / model.name
            if not model_path.exists():
                # Also check without extension variations
                found = False
                for ext in [".safetensors", ".ckpt", ".pt", ".pth", ".bin"]:
                    if (model_dir / (model.name + ext)).exists():
                        found = True
                        break
                    if model.name.lower().endswith(ext):
                        if (model_dir / model.name).exists():
                            found = True
                            break
                
                if not found:
                    missing.append(model)
        
        return missing
    
    @staticmethod
    def get_model_type_folder(model_type: str) -> str:
        """Get the ComfyUI folder name for a model type."""
        folders = {
            "checkpoint": "checkpoints",
            "lora": "loras",
            "vae": "vae",
            "controlnet": "controlnet",
            "upscaler": "upscale_models",
            "clip": "clip",
            "embedding": "embeddings",
            "style": "style_models",
            "gligen": "gligen",
            "ipadapter": "ipadapter",
        }
        return folders.get(model_type, model_type)
