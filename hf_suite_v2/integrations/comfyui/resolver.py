"""
ComfyUI model resolver - Match model names to HuggingFace repositories.

Uses a combination of:
- Known model mappings
- HuggingFace search
- Civitai search (optional)
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .parser import ModelReference

logger = logging.getLogger(__name__)


@dataclass
class ResolvedModel:
    """A model reference resolved to a downloadable source."""
    
    original: ModelReference
    repo_id: str
    platform: str = "huggingface"  # huggingface, civitai, modelscope
    file_path: Optional[str] = None  # Specific file in repo
    confidence: float = 1.0  # 0-1 confidence score
    
    @property
    def download_url(self) -> str:
        if self.platform == "huggingface":
            return f"https://huggingface.co/{self.repo_id}"
        elif self.platform == "civitai":
            return f"https://civitai.com/models/{self.repo_id}"
        return ""


class ComfyUIModelResolver:
    """
    Resolves ComfyUI model names to HuggingFace repositories.
    
    Usage:
        resolver = ComfyUIModelResolver()
        resolved = resolver.resolve(model_reference)
        if resolved:
            print(f"Found: {resolved.repo_id}")
    """
    
    # Known model name to HuggingFace repo mappings
    KNOWN_MAPPINGS = {
        # Stable Diffusion checkpoints
        "v1-5-pruned-emaonly.safetensors": ("runwayml/stable-diffusion-v1-5", "v1-5-pruned-emaonly.safetensors"),
        "v1-5-pruned.safetensors": ("runwayml/stable-diffusion-v1-5", "v1-5-pruned.safetensors"),
        "sd_xl_base_1.0.safetensors": ("stabilityai/stable-diffusion-xl-base-1.0", "sd_xl_base_1.0.safetensors"),
        "sd_xl_refiner_1.0.safetensors": ("stabilityai/stable-diffusion-xl-refiner-1.0", "sd_xl_refiner_1.0.safetensors"),
        "sd3_medium_incl_clips.safetensors": ("stabilityai/stable-diffusion-3-medium-diffusers", None),
        "sd3_medium_incl_clips_t5xxlfp16.safetensors": ("stabilityai/stable-diffusion-3-medium-diffusers", None),
        "flux1-dev.safetensors": ("black-forest-labs/FLUX.1-dev", "flux1-dev.safetensors"),
        "flux1-schnell.safetensors": ("black-forest-labs/FLUX.1-schnell", "flux1-schnell.safetensors"),
        
        # VAE
        "vae-ft-mse-840000-ema-pruned.safetensors": ("stabilityai/sd-vae-ft-mse", "vae-ft-mse-840000-ema-pruned.safetensors"),
        "sdxl_vae.safetensors": ("stabilityai/sdxl-vae", "sdxl_vae.safetensors"),
        "ae.safetensors": ("black-forest-labs/FLUX.1-dev", "ae.safetensors"),
        
        # CLIP
        "clip_l.safetensors": ("openai/clip-vit-large-patch14", None),
        "clip_g.safetensors": ("laion/CLIP-ViT-bigG-14-laion2B-39B-b160k", None),
        "t5xxl_fp16.safetensors": ("google/t5-v1_1-xxl", None),
        "t5xxl_fp8_e4m3fn.safetensors": ("comfyanonymous/flux_text_encoders", "t5xxl_fp8_e4m3fn.safetensors"),
        
        # ControlNet
        "control_v11p_sd15_canny.pth": ("lllyasviel/ControlNet-v1-1", "control_v11p_sd15_canny.pth"),
        "control_v11p_sd15_openpose.pth": ("lllyasviel/ControlNet-v1-1", "control_v11p_sd15_openpose.pth"),
        "control_v11f1p_sd15_depth.pth": ("lllyasviel/ControlNet-v1-1", "control_v11f1p_sd15_depth.pth"),
        
        # Upscalers
        "RealESRGAN_x4plus.pth": ("ai-forever/Real-ESRGAN", "RealESRGAN_x4plus.pth"),
        "RealESRGAN_x4plus_anime_6B.pth": ("ai-forever/Real-ESRGAN", "RealESRGAN_x4plus_anime_6B.pth"),
        "4x-UltraSharp.pth": ("Kim2091/4x-UltraSharp", "4x-UltraSharp.pth"),
    }
    
    # Model type to search tags
    TYPE_SEARCH_TAGS = {
        "checkpoint": ["stable-diffusion", "text-to-image"],
        "lora": ["lora", "stable-diffusion"],
        "vae": ["vae", "stable-diffusion"],
        "controlnet": ["controlnet"],
        "upscaler": ["super-resolution", "upscaler"],
        "embedding": ["textual-inversion", "embedding"],
    }
    
    def __init__(self, search_hf: bool = True, search_civitai: bool = False):
        """
        Initialize resolver.
        
        Args:
            search_hf: Whether to search HuggingFace for unknown models
            search_civitai: Whether to search Civitai for unknown models
        """
        self.search_hf = search_hf
        self.search_civitai = search_civitai
    
    def resolve(self, model: ModelReference) -> Optional[ResolvedModel]:
        """
        Resolve a model reference to a downloadable source.
        
        Args:
            model: ModelReference to resolve
            
        Returns:
            ResolvedModel if found, None otherwise
        """
        # Normalize name
        name = model.name.replace("\\", "/").split("/")[-1]
        
        # Check known mappings first
        if name in self.KNOWN_MAPPINGS:
            repo_id, file_path = self.KNOWN_MAPPINGS[name]
            return ResolvedModel(
                original=model,
                repo_id=repo_id,
                platform="huggingface",
                file_path=file_path,
                confidence=1.0,
            )
        
        # Try case-insensitive match
        name_lower = name.lower()
        for known_name, (repo_id, file_path) in self.KNOWN_MAPPINGS.items():
            if known_name.lower() == name_lower:
                return ResolvedModel(
                    original=model,
                    repo_id=repo_id,
                    platform="huggingface",
                    file_path=file_path,
                    confidence=0.95,
                )
        
        # Search HuggingFace
        if self.search_hf:
            result = self._search_huggingface(model)
            if result:
                return result
        
        return None
    
    def resolve_all(self, models: List[ModelReference]) -> Dict[str, Optional[ResolvedModel]]:
        """
        Resolve multiple model references.
        
        Returns:
            Dict mapping model name to resolved model (or None if not found)
        """
        results = {}
        for model in models:
            results[model.name] = self.resolve(model)
        return results
    
    def _search_huggingface(self, model: ModelReference) -> Optional[ResolvedModel]:
        """Search HuggingFace for a model."""
        try:
            from huggingface_hub import HfApi
            
            api = HfApi()
            
            # Build search query from model name
            name = model.name.replace("\\", "/").split("/")[-1]
            # Remove extension
            search_name = re.sub(r'\.(safetensors|ckpt|pt|pth|bin)$', '', name, flags=re.I)
            # Replace underscores/hyphens with spaces
            search_name = search_name.replace("_", " ").replace("-", " ")
            
            # Search
            results = list(api.list_models(
                search=search_name,
                limit=5,
                sort="downloads",
                direction=-1,
            ))
            
            if results:
                # Take the top result
                top = results[0]
                
                # Check if it seems like a match
                confidence = self._calculate_confidence(name, top.id)
                
                if confidence > 0.3:
                    return ResolvedModel(
                        original=model,
                        repo_id=top.id,
                        platform="huggingface",
                        confidence=confidence,
                    )
            
        except Exception as e:
            logger.warning(f"HuggingFace search failed: {e}")
        
        return None
    
    def _calculate_confidence(self, model_name: str, repo_id: str) -> float:
        """Calculate match confidence between model name and repo."""
        name_lower = model_name.lower()
        repo_lower = repo_id.lower()
        
        # Exact match in repo name
        repo_name = repo_id.split("/")[-1].lower()
        if name_lower.replace(".safetensors", "") in repo_name:
            return 0.9
        
        # Partial match
        name_parts = set(re.split(r'[-_\s.]+', name_lower))
        repo_parts = set(re.split(r'[-_\s.]+', repo_name))
        
        common = name_parts & repo_parts
        if len(common) > 0:
            return min(0.8, 0.3 + (len(common) / len(name_parts)) * 0.5)
        
        return 0.2
    
    @classmethod
    def get_known_models(cls) -> List[str]:
        """Get list of known model names."""
        return list(cls.KNOWN_MAPPINGS.keys())
    
    @classmethod
    def add_known_mapping(cls, model_name: str, repo_id: str, file_path: str = None) -> None:
        """Add a known model mapping."""
        cls.KNOWN_MAPPINGS[model_name] = (repo_id, file_path)
