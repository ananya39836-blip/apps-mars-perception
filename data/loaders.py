"""Dataset loaders and metadata structures for real and analogue imagery.
Chapter 23 & Chapter 39 / Tasks 13-14.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import numpy as np


@dataclass
class DatasetCard:
    name: str
    version: str
    source_url: str
    access_date: str
    licence: str
    citation: str
    num_images: int
    resolution: Tuple[int, int]
    channels: List[str]
    label_taxonomy_version: str
    known_limitations: str
    splits: Dict[str, List[str]]


class RealImageLoader:
    """Interface for real planetary / Earth analogue dataset loaders (e.g., AI4MARS).
    Requires explicit label mapping into Chapter 13 taxonomy.
    """
    def __init__(self, dataset_card: DatasetCard, label_mapping: Dict[int, int]):
        self.card = dataset_card
        self.label_mapping = label_mapping

    def load_scene(self, scene_id: str) -> Tuple[np.ndarray, Optional[np.ndarray], np.ndarray, Dict]:
        """Loads image, depth (or None), and mapped label mask."""
        raise NotImplementedError("Concrete loader required when real dataset is attached.")
