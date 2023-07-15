import json
import re
import time
import os
import requests

from datetime import datetime
from googleapiclient.http import MediaFileUpload
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from tqdm import tqdm

from rembg import remove

from PIL import Image

from ai_image_generator.enums.generated_image_status import GeneratedImageStatus
from ai_image_generator.models import GeneratedImage
from ai_image_generator.enums.image_detail_type import ImageDetailsType
from ai_image_generator.models import GeneratedImageItem


class LogoFolderUploader:
    def __init__(self, logos):
        self.drive = None
        self.logos = logos
        self.failed_task_ids = []
        self.taskIdList = []
        self.DRIVE_PARENT_AI_IMAGE_FOLDER_ID_TESTING = "1ci4SX32o601HjuIuPbdlRxy23VL9HMCh"
        self.DRIVE_PARENT_AI_IMAGE_FOLDER_ID = "14NyApQpa6WOk2-b4NAQLFGdPisOGr6mW"
        self.DEFAULT_DELAY_RESULT_TIME = 26
        self.DEFAULT_FIRST_DELAY_BEFORE_GET_TASK_ID = 60
        self.TARGET_IMAGE_SCALE = 2000
        self.MID_JOURNEY_API_KEY = "5bfd34fc-7c10-47c5-aea0-5a4a5c60a90c"
        self.PUSH_BULLET_API_KEY_LIST = ["o.ankZKMztYjmnGAW5bbOKI7cOykQpvq4o", "o.Br7OuGH6IeKRjAtkPEzXEDZNcZYq5UMj"]
        self.current_time = datetime.now().strftime("%d-%m-%Y_%I-%M-%p")

    def authenticate_google_drive(self):
        gauth = GoogleAuth()
        gauth.LoadCredentialsFile("googleCreds.txt")
        if gauth.credentials is None:
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            gauth.Refresh()
        else:
            gauth.Authorize()
        gauth.SaveCredentialsFile("googleCreds.txt")
        self.drive = GoogleDrive(gauth)

    def generate_image_mid_journey(self, description):
        # return "1449174024354196", self.get_image_from_task_id("1449174024354196")
        url = "https://api.midjourneyapi.io/v2/imagine"
        headers = {
            "Authorization": self.MID_JOURNEY_API_KEY,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "prompt": description + " [,isolated]"
        }

        image_url = ""
        task_id = ""
        try:
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 200:
                response_data = response.json()
                task_id = response_data.get("taskId")
                self.taskIdList.append(task_id)
                time.sleep(self.DEFAULT_FIRST_DELAY_BEFORE_GET_TASK_ID)
                image_url = self.get_image_from_task_id(task_id)
            else:
                image_url = ""
                self.failed_task_ids.append(
                    task_id + " - " + self.current_time + " - " + f"Request failed with status code: {response.status_code} (generateImageMidJourney)"
                )
                print("Request failed with status code:", response.status_code)
        except Exception as e:
            self.failed_task_ids.append(task_id + " - " + self.current_time + f" - {e}")
            print("Request failed with status code:", e)
        return task_id, image_url

    def get_image_from_task_id(self, task_id):
        url = "https://api.midjourneyapi.io/v2/result"
        headers = {
            "Authorization": f"{self.MID_JOURNEY_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "taskId": task_id,
        }

        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        status = response_data.get("status")
        image_url = response_data.get("imageURL")
        if response.status_code == (200 or 201):
            while status in ["pending", "running", "waiting-to-start"] or image_url is None or image_url == "":
                time.sleep(self.DEFAULT_DELAY_RESULT_TIME)
                response = requests.post(url, headers=headers, json=data)
                response_data = response.json()
                status = response_data.get("status")
                image_url = response_data.get("imageURL")
        else:
            self.failed_task_ids.append(
                task_id + " - " + self.current_time + " - " + f"Request failed with status code: {response.status_code} (getImageFromTaskId)"
            )
        return image_url

    def sanitize_folder_name(self, name):
        forbidden_chars = r'<>:"/\|?*'
        for char in forbidden_chars:
            name = name.replace(char, '')
        return name.strip()

    def create_logo_folders(self, logos, parent_folder):
        os.makedirs(parent_folder, exist_ok=True)
        logo_counter = 0

        with tqdm(total=len(logos), desc="Creating Logo Folders") as pbar:
            for logo in logos:
                title = logo["title"]
                tags = logo["tags"]
                description = logo["description"]
                logo_counter += 1

                task_id, mid_journey_image = self.generate_image_mid_journey(description)

                if task_id == "" or task_id is None:
                    print("There is an Empty TaskId !")
                    continue

                generated_image_id = self.save_generated_image_to_database(description, mid_journey_image, tags,
                                                                           task_id, title)

                if mid_journey_image == "" or mid_journey_image is None:
                    print("There is an Empty Image !")
                    generated_image = GeneratedImage.objects.get(id=generated_image_id)
                    generated_image.status = GeneratedImageStatus.FAILED
                    generated_image.save()
                    continue
                folder_name = self.sanitize_folder_name(title + f" ({generated_image_id})").replace(" ", "_")
                folder_path = os.path.join(parent_folder, folder_name)

                # Create folder for the logo
                os.makedirs(folder_path, exist_ok=True)

                self.add_logo_for_history_file(mid_journey_image, title, tags, description)
                try:
                    self.prepare_mid_journey_images(mid_journey_image, folder_path)
                except Exception as e:
                    print(e)
                    continue

                self.create_logo_folder(folder_path, title, tags, description, generated_image_id)
                pbar.update(1)

    def extract_generated_image_id_from_image_folder_name(self, image_file_name):
        # Extract the number within parentheses using regular expressions
        match = re.search(r'\((\d+)\)', image_file_name)
        extracted_number = -1
        if match:
            extracted_number = match.group(1)
            print(extracted_number)  # Output: 2
        else:
            print(f"No image id found in {image_file_name} folder name.")
        return extracted_number

    def save_generated_image_to_database(self, description, mid_journey_image, tags, task_id, title):
        generated_image = GeneratedImage(title=title, tags=tags, description=description,
                                         platform_image_url=mid_journey_image, task_id=task_id)
        generated_image.save()
        generated_image_id = generated_image.id
        return generated_image_id

    def create_logo_folder(self, folder_path, logoTitle, logoTags, logoDescription, generated_image_id):
        logo_file_path = os.path.join(folder_path, f"logo_description.txt")
        with open(logo_file_path, 'w') as file:
            file.write(f"Logo: {logoTitle}\n")
            file.write(f"Tags: {', '.join(logoTags)}\n")
            file.write(f"Description: {logoDescription}")

    def add_logo_for_history_file(self, image_list, logoTitle, logoTags, logoDescription):
        history_logs_path = os.path.join("history_logs.txt")
        with open(history_logs_path, "a") as file:
            file.write(f"{logoTitle}\n")
            file.write(f"Tags: {', '.join(logoTags)}\n")
            file.write(f"Description: {logoDescription}\n\n")
            file.write(f"ImageUrls {image_list}\n")

    def get_last_item_image_id(self):
        last_item = GeneratedImageItem.objects.last()
        return last_item.id

    def download_image(self, image_list, folder_path):
        image_counter = 0
        for image in image_list:
            image_counter += 1
            image_path = os.path.join(folder_path, f"logo_image({image_counter}).png")
            response = requests.get(image)
            with open(image_path, 'wb') as file:
                file.write(response.content)

    def prepare_mid_journey_images(self, image_url, folder_path):
        image_path = os.path.join(folder_path, f"image(main).png")
        response = requests.get(image_url)
        with open(image_path, 'wb') as file:
            file.write(response.content)
        self.prepare_image(image_path, folder_path)

    def upscale_image(self, image_path, folder_path, new_image_name):
        upscale_image_path = f"{folder_path}/{new_image_name}"
        image = Image.open(image_path)
        width, height = image.size
        target_height = int(self.TARGET_IMAGE_SCALE * height / width)
        resized_image = image.resize((self.TARGET_IMAGE_SCALE, target_height))
        resized_image.save(upscale_image_path)
        return upscale_image_path

    def remove_background(self, image_path, folder_path, image_name):
        input_image = Image.open(image_path)
        output_image = remove(input_image)
        save_path = f"{folder_path}/{image_name}"
        output_image.save(save_path, format="PNG")

    def prepare_image(self, image_path, folder_path):
        image = Image.open(image_path)
        width, height = image.size
        split_width = width // 2
        split_height = height // 2

        top_left = image.crop((0, 0, split_width, split_height))
        top_right = image.crop((split_width, 0, width, split_height))
        bottom_left = image.crop((0, split_height, split_width, height))
        bottom_right = image.crop((split_width, split_height, width, height))

        top_left_path = os.path.join(folder_path, "image(1).png")
        top_right_path = os.path.join(folder_path, "image(2).png")
        bottom_left_path = os.path.join(folder_path, "image(3).png")
        bottom_right_path = os.path.join(folder_path, "image(4).png")

        top_left.save(top_left_path)
        top_right.save(top_right_path)
        bottom_left.save(bottom_left_path)
        bottom_right.save(bottom_right_path)

        upscale_image_path_1 = self.upscale_image(top_left_path, folder_path, "up_scaled_image(1).png")
        upscale_image_path_2 = self.upscale_image(top_right_path, folder_path, "up_scaled_image(2).png")
        upscale_image_path_3 = self.upscale_image(bottom_left_path, folder_path, "up_scaled_image(3).png")
        upscale_image_path_4 = self.upscale_image(bottom_right_path, folder_path, "up_scaled_image(4).png")

        self.remove_background(upscale_image_path_1, folder_path, "removed_bg_image(1).png")
        self.remove_background(upscale_image_path_2, folder_path, "removed_bg_image(2).png")
        self.remove_background(upscale_image_path_3, folder_path, "removed_bg_image(3).png")
        self.remove_background(upscale_image_path_4, folder_path, "removed_bg_image(4).png")

    def upload_folder_to_drive(self, folder_path):
        uploaded_folder_counter = 0
        folder_name = os.path.basename(folder_path)
        folder_metadata = {
            'title': folder_name,
            'parents': [{'id': self.DRIVE_PARENT_AI_IMAGE_FOLDER_ID}],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = self.drive.CreateFile(folder_metadata)
        folder.Upload(param={'supportsAllDrives': True})

        last_generated_item_image_id = self.get_last_item_image_id()

        for root, dirs, files in os.walk(folder_path):
            for dir in dirs:
                uploaded_folder_counter += 1
                sub_folder_path = os.path.join(root, dir)
                sub_folder_name = os.path.basename(sub_folder_path)
                sub_folder_metadata = {
                    'title': sub_folder_name,
                    'parents': [{'id': folder['id']}],
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                sub_folder = self.drive.CreateFile(sub_folder_metadata)
                sub_folder.Upload(param={'supportsAllDrives': True})

                sub_folder.InsertPermission({
                    'type': 'anyone',
                    'role': 'reader',
                })

                drive_folder_image_url = sub_folder['alternateLink']

                generated_image_id = self.extract_generated_image_id_from_image_folder_name(sub_folder_name)
                generated_image = GeneratedImage.objects.get(id=int(generated_image_id))
                self.update_generated_drive_folder_url_database(drive_folder_image_url, generated_image)

                for file_name in os.listdir(sub_folder_path):
                    file_path = os.path.join(sub_folder_path, file_name)

                    if "image" in str(file_name):
                        last_generated_item_image_id = last_generated_item_image_id + 1
                        drive_image_file_name = str(last_generated_item_image_id) + " - " + str(file_name)
                    else:
                        drive_image_file_name = file_name

                    file_metadata = {
                        'title': drive_image_file_name,
                        'parents': [{'id': sub_folder['id']}]
                    }
                    media = MediaFileUpload(file_path)
                    file = self.drive.CreateFile(file_metadata)
                    file.SetContentFile(file_path)
                    file.Upload(param={'supportsAllDrives': True, 'media_body': media})
                    file.InsertPermission({
                        'type': 'anyone',
                        'role': 'reader',
                    })

                    drive_image_url = file['alternateLink']
                    if "image" in str(file_name):
                        image_type = self.get_image_type_from_image_file_name(file_name)
                        if image_type == ImageDetailsType.MAIN:
                            generated_image.drive_image_url = drive_image_url
                            generated_image.save()
                        print(file_name)
                        generated_image_item = GeneratedImageItem(generated_image_id=generated_image_id,
                                                                  image_type=image_type, image_url=drive_image_url)
                        generated_image_item.save()

                generated_image.status = GeneratedImageStatus.SUCCESS
                generated_image.save()

        return uploaded_folder_counter

    def get_image_type_from_image_file_name(self, file_name):
        if re.match(r"image\(\d+\).png", file_name):
            return ImageDetailsType.SPLITTED
        elif re.match(r"removed_bg_image\(\d+\).png", file_name):
            return ImageDetailsType.REMOVED_BACKGROUND
        elif re.match(r"up_scaled_image\(\d+\).png", file_name):
            return ImageDetailsType.UP_SCALED
        elif file_name == "image(main).png":
            return ImageDetailsType.MAIN
        else:
            return None

    def update_generated_drive_folder_url_database(self, drive_folder_image_url, generate_image):
        generate_image.drive_folder_url = drive_folder_image_url
        generate_image.save()

    def send_push_bullet_notification(self, uploaded_folder_counter):
        for api_key in self.PUSH_BULLET_API_KEY_LIST:
            headers = {
                "Access-Token": api_key,
                "Content-Type": "application/json"
            }
            data = {
                "type": "note",
                "title": "Logo Folders Uploaded",
                "body": f"Logo folders and images have been uploaded to Google Drive. Total files uploaded: {uploaded_folder_counter}"
            }
            response = requests.post("https://api.pushbullet.com/v2/pushes", headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                print(f"Notification sent successfully to {api_key}.")
            else:
                print(f"Failed to send notification {api_key} .")

    def save_failed_task_ids(self, failed_task_ids):
        file_path = os.path.join("failed_task_ids.txt")
        with open(file_path, "a") as file:
            for task_id in failed_task_ids:
                file.write(task_id + "\n")

    def save_task_ids(self, taskIdList):
        file_path = os.path.join("task_id.txt")
        with open(file_path, "a") as file:
            for task_id in taskIdList:
                file.write(task_id + f" - {self.current_time}" + "\n")

    def upload_logos(self):
        self.authenticate_google_drive()

        parent_folder = f'generated_images/logo_folders_{self.current_time}'

        self.create_logo_folders(self.logos, parent_folder)

        uploaded_folders_count = self.upload_folder_to_drive(parent_folder)

        self.send_push_bullet_notification(uploaded_folders_count)

        # self.save_task_ids(self.taskIdList)
        #
        # self.save_failed_task_ids(self.failed_task_ids)

        print("Logo folders, text files, and images have been created and downloaded.")
