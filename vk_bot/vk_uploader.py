import aiohttp
from vk_bot.vk_client import vk_client
from app.logger import logger
import os

class VkUploader:
    async def upload_photo_messages(self, peer_id: int, file_path: str) -> str | None:
        """Uploads a photo for a message and returns the attachment string."""
        # 1. Get upload server
        try:
            upload_server_data = await vk_client._request("photos.getMessagesUploadServer", {"peer_id": peer_id})
            upload_url = upload_server_data["upload_url"]
        except Exception as e:
            logger.error(f"Failed to get upload server: {e}")
            return None

        # 2. Upload file
        async with aiohttp.ClientSession() as session:
            with open(file_path, "rb") as f:
                form = aiohttp.FormData()
                form.add_field('photo', f, filename=os.path.basename(file_path), content_type='image/jpeg')
                
                async with session.post(upload_url, data=form) as resp:
                    upload_result = await resp.json()

        # 3. Save photo
        if "photo" not in upload_result or not upload_result["photo"] or upload_result["photo"] == '[]':
            logger.error(f"VK Upload failed: {upload_result}")
            return None

        save_params = {
            "photo": upload_result["photo"],
            "server": upload_result["server"],
            "hash": upload_result["hash"]
        }
        
        try:
            saved_photos = await vk_client._request("photos.saveMessagesPhoto", save_params)
            if saved_photos and len(saved_photos) > 0:
                photo = saved_photos[0]
                owner_id = photo["owner_id"]
                photo_id = photo["id"]
                access_key = photo.get("access_key")
                attachment = f"photo{owner_id}_{photo_id}"
                if access_key:
                    attachment += f"_{access_key}"
                return attachment
        except Exception as e:
            logger.error(f"Failed to save uploaded photo: {e}")
            
        return None

vk_uploader = VkUploader()
