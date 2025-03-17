import json
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass

import dacite
import aiohttp

from enums import PayloadData

# ... existing code ...

@dataclass
class Image_info:
    id: str
    name: Any
    description: Any
    datetime: Any
    type: Any
    animated: Any
    width: Any
    height: Any
    size: Any
    views: Any
    bandwidth: Any
    vote: Any
    favorite: Any
    nsfw: Any
    section: Any
    account_url: Any
    account_id: Any
    is_ad: Any
    in_most_viral: Any
    has_sound: Any
    tags: Any
    ad_type: Any
    ad_url: Any
    edited: Any
    in_gallery: Any
    deletehash: Any
    link: Any

# Add new data classes for other Imgur entities
@dataclass
class Album_info:
    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    datetime: Optional[int] = None
    cover: Optional[str] = None
    cover_width: Optional[int] = None
    cover_height: Optional[int] = None
    account_url: Optional[str] = None
    account_id: Optional[int] = None
    privacy: Optional[str] = None
    layout: Optional[str] = None
    views: Optional[int] = None
    link: Optional[str] = None
    favorite: Optional[bool] = None
    nsfw: Optional[bool] = None
    section: Optional[str] = None
    images_count: Optional[int] = None
    images: Optional[List[Image_info]] = None
    in_gallery: Optional[bool] = None
    deletehash: Optional[str] = None

@dataclass
class Comment_info:
    id: int
    image_id: str
    comment: str
    author: str
    author_id: int
    on_album: bool
    album_cover: Optional[str] = None
    ups: Optional[int] = None
    downs: Optional[int] = None
    points: Optional[int] = None
    datetime: Optional[int] = None
    parent_id: Optional[int] = None
    deleted: Optional[bool] = None
    vote: Optional[Any] = None
    children: Optional[List["Comment_info"]] = None

@dataclass
class Response:
    success: Any
    status: Any
    data: dict

@dataclass
class RateLimits:
    client_limit: int = 12500
    client_remaining: int = 12500
    client_reset: int = 0
    user_limit: Optional[int] = None
    user_remaining: Optional[int] = None
    user_reset: Optional[int] = None

# Add exception classes
class ImgurAPIError(Exception):
    def __init__(self, message, status=None, response=None):
        self.message = message
        self.status = status
        self.response = response
        super().__init__(self.message)

class RateLimitExceeded(ImgurAPIError):
    def __init__(self, message, reset_time=None):
        self.reset_time = reset_time
        super().__init__(message)

class Imgur:
    BASE_URL = "https://api.imgur.com/3/"
    
    def __init__(
        self, 
        client_id: str, 
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        
        # Set up headers based on authentication method
        self.headers = self._get_headers()
        
        # Rate limit tracking
        self._rate_limits = RateLimits()
        
        # Session for connection pooling
        self._session = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Generate headers for API requests."""
        headers = {}
        
        # Authentication headers
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        else:
            headers["Authorization"] = f"Client-ID {self.client_id}"
            
        return headers
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Close the aiohttp session."""
        if self._session:
            await self._session.close()
            self._session = None
    
    def _update_rate_limits(self, response):
        """Update rate limit information from response headers."""
        headers = response.headers
        
        # Client rate limits
        if "X-RateLimit-ClientLimit" in headers:
            self._rate_limits.client_limit = int(headers["X-RateLimit-ClientLimit"])
        if "X-RateLimit-ClientRemaining" in headers:
            self._rate_limits.client_remaining = int(headers["X-RateLimit-ClientRemaining"])
        if "X-RateLimit-ClientReset" in headers:
            self._rate_limits.client_reset = int(headers["X-RateLimit-ClientReset"])
            
        # User rate limits (only present with OAuth)
        if "X-RateLimit-UserLimit" in headers:
            self._rate_limits.user_limit = int(headers["X-RateLimit-UserLimit"])
        if "X-RateLimit-UserRemaining" in headers:
            self._rate_limits.user_remaining = int(headers["X-RateLimit-UserRemaining"])
        if "X-RateLimit-UserReset" in headers:
            self._rate_limits.user_reset = int(headers["X-RateLimit-UserReset"])
    
    @property
    def rate_limits(self) -> RateLimits:
        """Get current rate limit information."""
        return self._rate_limits

    async def get_request(self, url, payload=None):
        session = await self._get_session()
        
        async with session.get(url, headers=self.headers, data=payload) as resp:
            # Update rate limits from response headers
            self._update_rate_limits(resp)
            
            # Check for rate limit errors
            if resp.status == 429:
                reset_time = int(resp.headers.get("X-RateLimit-ClientReset", 0))
                raise RateLimitExceeded(
                    f"Rate limit exceeded. Reset in {reset_time} seconds.",
                    reset_time=reset_time
                )
            
            # Fix: Call raise_for_status() with parentheses
            resp.raise_for_status()
            
            response_data = json.loads(await resp.text())
            return response_data

    async def post_request(self, url, payload):
        session = await self._get_session()
        
        async with session.post(url, headers=self.headers, data=payload) as resp:
            # Update rate limits from response headers
            self._update_rate_limits(resp)
            
            # Fix: Call raise_for_status() with parentheses
            resp.raise_for_status()
            
            response_data = json.loads(await resp.text())
            return response_data

    async def delete_request(self, url):
        """Make a DELETE request to the Imgur API."""
        session = await self._get_session()
        
        async with session.delete(url, headers=self.headers) as resp:
            # Update rate limits from response headers
            self._update_rate_limits(resp)
            
            # Fix: Call raise_for_status() with parentheses
            resp.raise_for_status()
            
            response_data = json.loads(await resp.text())
            return response_data

    async def get_image(self, image_hash):
        """
        Get information about an image.
        
        Args:
            image_hash: The ID of the image
            
        Returns:
            Tuple of (Image_info, Response)
        """
        response = await self.get_request(f"{self.BASE_URL}image/{image_hash}")
        image_data = dacite.from_dict(data_class=Image_info, data=response["data"])
        api_response = dacite.from_dict(data_class=Response, data=response)
        return image_data, api_response

    async def upload_image(
        self,
        title: str = None,
        description: str = None,
        name: str = None,
        image: str = None,
        video: str = None,
    ):
        """
        Uploads an Image to Imgur API using the provided Client ID.

        :param title
        :param description
        :param name
        :param image: must be a url or bytes.
        :param video: must be bytes.
        """
        payload = PayloadData(
            title=title, description=description, name=name, image=image, video=video
        ).payload
        response = await self.post_request(f"{self.BASE_URL}image", payload)
        image_data = dacite.from_dict(data_class=Image_info, data=response["data"])
        api_response = dacite.from_dict(data_class=Response, data=response)
        return image_data, api_response
    
    async def delete_image(self, image_hash: str):
        """
        Delete an image from Imgur.
        
        Args:
            image_hash: The ID of the image to delete
            
        Returns:
            Tuple of (bool, Response) indicating success
        """
        response = await self.delete_request(f"{self.BASE_URL}image/{image_hash}")
        api_response = dacite.from_dict(data_class=Response, data=response)
        return response.get("success", False), api_response
    
    async def create_album(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        images: Optional[List[str]] = None,
        privacy: Optional[str] = None,
        layout: Optional[str] = None,
        cover: Optional[str] = None
    ):
        """
        Create a new album.
        
        Args:
            title: The title of the album
            description: The description of the album
            images: List of image IDs to include in the album
            privacy: Privacy level of the album (public, hidden, secret)
            layout: Layout of the album (blog, grid, horizontal, vertical)
            cover: The ID of the cover image
            
        Returns:
            Tuple of (Album_info, Response)
        """
        payload = {}
        if title:
            payload["title"] = title
        if description:
            payload["description"] = description
        if privacy:
            payload["privacy"] = privacy
        if layout:
            payload["layout"] = layout
        if cover:
            payload["cover"] = cover
            
        # Handle image IDs
        if images:
            for i, img_id in enumerate(images):
                payload[f"ids[{i}]"] = img_id
                
        response = await self.post_request(f"{self.BASE_URL}album", payload)
        album_data = dacite.from_dict(data_class=Album_info, data=response["data"])
        api_response = dacite.from_dict(data_class=Response, data=response)
        return album_data, api_response
    
    async def get_album(self, album_hash: str):
        """
        Get information about an album.
        
        Args:
            album_hash: The ID of the album
            
        Returns:
            Tuple of (Album_info, Response)
        """
        response = await self.get_request(f"{self.BASE_URL}album/{album_hash}")
        album_data = dacite.from_dict(data_class=Album_info, data=response["data"])
        api_response = dacite.from_dict(data_class=Response, data=response)
        return album_data, api_response
    
    async def add_images_to_album(self, album_hash: str, images: List[str]):
        """
        Add images to an existing album.
        
        Args:
            album_hash: The ID of the album
            images: List of image IDs to add
            
        Returns:
            Tuple of (bool, Response) indicating success
        """
        payload = {}
        for i, img_id in enumerate(images):
            payload[f"ids[{i}]"] = img_id
            
        response = await self.post_request(f"{self.BASE_URL}album/{album_hash}/add", payload)
        api_response = dacite.from_dict(data_class=Response, data=response)
        return response.get("success", False), api_response
    
    async def get_account_images(self):
        """
        Get images for the authenticated user.
        Requires OAuth authentication.
        
        Returns:
            Tuple of (List[Image_info], Response)
        """
        if not self.access_token:
            raise ImgurAPIError("OAuth authentication required for this endpoint")
            
        response = await self.get_request(f"{self.BASE_URL}account/me/images")
        images = [
            dacite.from_dict(data_class=Image_info, data=img_data)
            for img_data in response["data"]
        ]
        api_response = dacite.from_dict(data_class=Response, data=response)
        return images, api_response
    
    async def get_account_albums(self):
        """
        Get albums for the authenticated user.
        Requires OAuth authentication.
        
        Returns:
            Tuple of (List[Album_info], Response)
        """
        if not self.access_token:
            raise ImgurAPIError("OAuth authentication required for this endpoint")
            
        response = await self.get_request(f"{self.BASE_URL}account/me/albums")
        albums = [
            dacite.from_dict(data_class=Album_info, data=album_data)
            for album_data in response["data"]
        ]
        api_response = dacite.from_dict(data_class=Response, data=response)
        return albums, api_response
    
    async def favorite_image(self, image_hash: str):
        """
        Favorite an image.
        Requires OAuth authentication.
        
        Args:
            image_hash: The ID of the image to favorite
            
        Returns:
            Tuple of (bool, Response) indicating success
        """
        if not self.access_token:
            raise ImgurAPIError("OAuth authentication required for this endpoint")
            
        response = await self.post_request(f"{self.BASE_URL}image/{image_hash}/favorite", {})
        api_response = dacite.from_dict(data_class=Response, data=response)
        return response.get("success", False), api_response
    
    async def get_gallery_image(self, gallery_hash: str):
        """
        Get information about a gallery image.
        
        Args:
            gallery_hash: The ID of the gallery image
            
        Returns:
            Tuple of (Image_info, Response)
        """
        response = await self.get_request(f"{self.BASE_URL}gallery/image/{gallery_hash}")
        image_data = dacite.from_dict(data_class=Image_info, data=response["data"])
        api_response = dacite.from_dict(data_class=Response, data=response)
        return image_data, api_response
    
        async def get_account(self, username: str):
        """
        Get information about an account.
        
        Args:
            username: The username of the account
            
        Returns:
            Tuple of (Account_info, Response)
        """
        response = await self.get_request(f"{self.BASE_URL}account/{username}")
        account_data = dacite.from_dict(data_class=Account_info, data=response["data"])
        api_response = dacite.from_dict(data_class=Response, data=response)
        return account_data, api_response
        
    async def get_account_images(self):
        """
        Get images for the authenticated user.
        Requires OAuth authentication.
        
        Returns:
            Tuple of (List[Image_info], Response)
        """
        if not self.access_token:
            raise ImgurAPIError("OAuth authentication required for this endpoint")
            
        response = await self.get_request(f"{self.BASE_URL}account/me/images")
        images = [
            dacite.from_dict(data_class=Image_info, data=img_data)
            for img_data in response["data"]
        ]
        api_response = dacite.from_dict(data_class=Response, data=response)
        return images, api_response
    
    async def get_account_albums(self):
        """
        Get albums for the authenticated user.
        Requires OAuth authentication.
        
        Returns:
            Tuple of (List[Album_info], Response)
        """
        if not self.access_token:
            raise ImgurAPIError("OAuth authentication required for this endpoint")
            
        response = await self.get_request(f"{self.BASE_URL}account/me/albums")
        albums = [
            dacite.from_dict(data_class=Album_info, data=album_data)
            for album_data in response["data"]
        ]
        api_response = dacite.from_dict(data_class=Response, data=response)
        return albums, api_response
    
    async def get_comment(self, comment_id: int):
        """
        Get information about a comment.
        
        Args:
            comment_id: The ID of the comment
            
        Returns:
            Tuple of (Comment_info, Response)
        """
        response = await self.get_request(f"{self.BASE_URL}comment/{comment_id}")
        comment_data = dacite.from_dict(data_class=Comment_info, data=response["data"])
        api_response = dacite.from_dict(data_class=Response, data=response)
        return comment_data, api_response
    
    async def create_comment(self, image_id: str, comment: str, parent_id: Optional[int] = None):
        """
        Create a comment on an image.
        Requires OAuth authentication.
        
        Args:
            image_id: The ID of the image to comment on
            comment: The comment text
            parent_id: The ID of the parent comment (for replies)
            
        Returns:
            Tuple of (int, Response) with the new comment ID
        """
        if not self.access_token:
            raise ImgurAPIError("OAuth authentication required for this endpoint")
            
        payload = {"image_id": image_id, "comment": comment}
        if parent_id:
            payload["parent_id"] = parent_id
            
        response = await self.post_request(f"{self.BASE_URL}comment", payload)
        comment_id = response["data"]["id"]
        api_response = dacite.from_dict(data_class=Response, data=response)
        return comment_id, api_response
    
    async def delete_comment(self, comment_id: int):
        """
        Delete a comment.
        Requires OAuth authentication.
        
        Args:
            comment_id: The ID of the comment to delete
            
        Returns:
            Tuple of (bool, Response) indicating success
        """
        if not self.access_token:
            raise ImgurAPIError("OAuth authentication required for this endpoint")
            
        response = await self.delete_request(f"{self.BASE_URL}comment/{comment_id}")
        api_response = dacite.from_dict(data_class=Response, data=response)
        return response.get("success", False), api_response
    
    async def search_gallery(self, query: str, sort: str = "time", window: str = "all", page: int = 0):
        """
        Search the gallery.
        
        Args:
            query: Query string
            sort: Sort method (time, viral, top)
            window: Time window (day, week, month, year, all)
            page: Page number
            
        Returns:
            Tuple of (List[Image_info or Album_info], Response)
        """
        params = {
            "q": query,
            "sort": sort,
            "window": window,
            "page": page
        }
        
        url = f"{self.BASE_URL}gallery/search?{self._build_query_params(params)}"
        response = await self.get_request(url)
        
        # Gallery can return both images and albums
        items = []
        for item_data in response["data"]:
            if "is_album" in item_data and item_data["is_album"]:
                items.append(dacite.from_dict(data_class=Album_info, data=item_data))
            else:
                items.append(dacite.from_dict(data_class=Image_info, data=item_data))
                
        api_response = dacite.from_dict(data_class=Response, data=response)
        return items, api_response
    
    def _build_query_params(self, params: Dict[str, Any]) -> str:
        """Build query parameters for URL."""
        return "&".join([f"{k}={v}" for k, v in params.items() if v is not None])
    
    async def get_gallery(self, section: str = "hot", sort: str = "viral", window: str = "day", page: int = 0):
        """
        Get images from the gallery.
        
        Args:
            section: Section (hot, top, user)
            sort: Sort method (viral, top, time, rising)
            window: Time window (day, week, month, year, all)
            page: Page number
            
        Returns:
            Tuple of (List[Image_info or Album_info], Response)
        """
        params = {
            "sort": sort,
            "window": window,
            "page": page
        }
        
        url = f"{self.BASE_URL}gallery/{section}?{self._build_query_params(params)}"
        response = await self.get_request(url)
        
        # Gallery can return both images and albums
        items = []
        for item_data in response["data"]:
            if "is_album" in item_data and item_data["is_album"]:
                items.append(dacite.from_dict(data_class=Album_info, data=item_data))
            else:
                items.append(dacite.from_dict(data_class=Image_info, data=item_data))
                
        api_response = dacite.from_dict(data_class=Response, data=response)
        return items, api_response
    
    async def upload_image_from_file(
        self,
        file_path: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        name: Optional[str] = None
    ):
        """
        Upload an image from a local file.
        
        Args:
            file_path: Path to the local file
            title: Title for the image
            description: Description for the image
            name: Name for the image
            
        Returns:
            Tuple of (Image_info, Response)
        """
        with open(file_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
            
        return await self.upload_image(
            title=title,
            description=description,
            name=name,
            image=image_data
        )
    
    async def refresh_access_token(self):
        """
        Refresh the OAuth access token using the refresh token.
        
        Returns:
            Dict with new tokens
        """
        if not self.client_secret or not self.refresh_token:
            raise ImgurAPIError("Client secret and refresh token are required")
            
        payload = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.imgur.com/oauth2/token", data=payload) as resp:
                resp.raise_for_status()
                token_data = json.loads(await resp.text())
                
                # Update tokens
                self.access_token = token_data["access_token"]
                self.refresh_token = token_data["refresh_token"]
                
                # Update headers with new access token
                self.headers = self._get_headers()
                
                return token_data
    
    async def get_image_comments(self, image_id: str, sort: str = "best"):
        """
        Get comments for an image.
        
        Args:
            image_id: The ID of the image
            sort: Sort method (best, top, new)
            
        Returns:
            Tuple of (List[Comment_info], Response)
        """
        response = await self.get_request(f"{self.BASE_URL}image/{image_id}/comments/{sort}")
        
        # Process nested comments
        def process_comments(comments_data):
            result = []
            for comment_data in comments_data:
                comment = dacite.from_dict(data_class=Comment_info, data=comment_data)
                
                # Process children recursively if they exist
                if "children" in comment_data and comment_data["children"]:
                    comment.children = process_comments(comment_data["children"])
                    
                result.append(comment)
            return result
            
        comments = process_comments(response["data"])
        api_response = dacite.from_dict(data_class=Response, data=response)
        return comments, api_response