from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Union


@dataclass
class PayloadData:
    """Class for handling payload data for Imgur API requests."""
    
    title: Optional[str] = None
    description: Optional[str] = None
    name: Optional[str] = None
    image: Optional[Union[str, bytes]] = None
    video: Optional[bytes] = None
    album: Optional[str] = None
    ids: Optional[List[str]] = None
    privacy: Optional[str] = None
    layout: Optional[str] = None
    cover: Optional[str] = None
    
    @property
    def payload(self) -> Dict[str, Any]:
        """Convert the dataclass to a dictionary for API requests."""
        payload = {}
        
        for key, value in self.__dict__.items():
            if value is not None:
                if key == 'ids' and isinstance(value, list):
                    # Handle list of image IDs for albums
                    for i, img_id in enumerate(value):
                        payload[f'ids[{i}]'] = img_id
                else:
                    payload[key] = value
                    
        return payload